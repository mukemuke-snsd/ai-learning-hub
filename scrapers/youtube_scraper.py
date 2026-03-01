"""YouTube 抓取器 - RSS + 字幕提取"""

import re
import time
from datetime import datetime, timedelta
from typing import Optional

import feedparser
import requests

from config.loader import load_module_config, load_settings
from scrapers.base_scraper import BaseScraper

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    HAS_TRANSCRIPT_API = True
except ImportError:
    HAS_TRANSCRIPT_API = False


class YouTubeScraper(BaseScraper):
    """YouTube 频道内容抓取器"""

    def __init__(self, module: str = "product_radar",
                 fetch_transcripts: bool = True):
        self.module = module
        self.fetch_transcripts = fetch_transcripts
        self.module_cfg = load_module_config(module)
        settings = load_settings()
        scraper_cfg = settings.get("scraper", {})

        self.channels = self.module_cfg.get("youtube_channels", [])
        self.keywords = self.module_cfg.get("keywords", {})
        self.timeout = scraper_cfg.get("request_timeout", 15)
        self.delay = scraper_cfg.get("request_delay", 1)
        self.max_age_days = scraper_cfg.get("max_article_age_days", 7)
        self.user_agent = scraper_cfg.get("user_agent", "AI-Learning-Hub/1.0")

    def fetch_all(self, verbose: bool = True) -> list:
        all_items = []
        for channel in self.channels:
            if verbose:
                print(f"  📺 抓取 YouTube: {channel['name']}...")
            try:
                items = self._fetch_channel(channel)
                all_items.extend(items)
                if verbose:
                    print(f"     ✅ 获取 {len(items)} 个视频")
            except Exception as e:
                if verbose:
                    print(f"     ❌ 失败: {str(e)[:80]}")
            time.sleep(self.delay)

        # 抓取播客
        for podcast in self.module_cfg.get("podcast_feeds", []):
            if verbose:
                print(f"  🎙 抓取播客: {podcast['name']}...")
            try:
                items = self._fetch_podcast(podcast)
                all_items.extend(items)
                if verbose:
                    print(f"     ✅ 获取 {len(items)} 个节目")
            except Exception as e:
                if verbose:
                    print(f"     ❌ 失败: {str(e)[:80]}")
            time.sleep(self.delay)

        return all_items

    def _fetch_channel(self, channel: dict) -> list:
        rss_url = channel.get("rss_url", "")
        if not rss_url:
            channel_id = channel.get("channel_id", "")
            if channel_id:
                rss_url = (
                    f"https://www.youtube.com/feeds/videos.xml"
                    f"?channel_id={channel_id}"
                )
            else:
                return []

        headers = {"User-Agent": self.user_agent}
        try:
            response = requests.get(
                rss_url, headers=headers, timeout=self.timeout
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception(f"HTTP 请求失败: {e}")

        feed = feedparser.parse(response.content)
        items = []
        cutoff = datetime.now() - timedelta(days=self.max_age_days)

        for entry in feed.entries[:10]:
            item = self._parse_youtube_entry(entry, channel)
            if item is None:
                continue

            if item["published_at"]:
                try:
                    pub = datetime.fromisoformat(
                        item["published_at"].replace("Z", "+00:00")
                    )
                    if pub.replace(tzinfo=None) < cutoff:
                        continue
                except (ValueError, TypeError):
                    pass

            item["relevance_score"] = self._calculate_relevance(item)
            items.append(item)

        return items

    def _parse_youtube_entry(self, entry, channel: dict) -> Optional[dict]:
        title = getattr(entry, "title", "")
        link = getattr(entry, "link", "")
        if not title or not link:
            return None

        summary = ""
        if hasattr(entry, "summary"):
            summary = entry.summary[:500]
        elif hasattr(entry, "media_group") and entry.media_group:
            desc = getattr(entry.media_group[0], "media_description", None)
            if desc:
                summary = str(desc)[:500]

        published_at = ""
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                published_at = datetime(
                    *entry.published_parsed[:6]
                ).isoformat()
            except (TypeError, ValueError):
                pass

        video_id = self._extract_video_id(link)

        transcript = ""
        if video_id and HAS_TRANSCRIPT_API and self.fetch_transcripts:
            transcript = self.fetch_transcript(video_id, channel.get("language", "en"))

        return self.make_content_item(
            module=self.module,
            content_type="video",
            title=title.strip(),
            url=link.strip(),
            source=channel["name"],
            platform="youtube",
            category="youtube",
            summary=summary,
            content=transcript[:5000] if transcript else "",
            transcript=transcript,
            creator_name=channel["name"],
            published_at=published_at,
        )

    def _fetch_podcast(self, podcast: dict) -> list:
        rss_url = podcast.get("rss_url", "")
        if not rss_url:
            return []

        headers = {"User-Agent": self.user_agent}
        try:
            response = requests.get(
                rss_url, headers=headers, timeout=self.timeout
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception(f"HTTP 请求失败: {e}")

        feed = feedparser.parse(response.content)
        items = []
        cutoff = datetime.now() - timedelta(days=self.max_age_days)

        for entry in feed.entries[:5]:
            title = getattr(entry, "title", "")
            link = getattr(entry, "link", "")
            if not title or not link:
                continue

            summary = ""
            if hasattr(entry, "summary"):
                from bs4 import BeautifulSoup
                summary = BeautifulSoup(
                    entry.summary, "html.parser"
                ).get_text(strip=True)[:500]

            published_at = ""
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    published_at = datetime(
                        *entry.published_parsed[:6]
                    ).isoformat()
                except (TypeError, ValueError):
                    pass

            if published_at:
                try:
                    pub = datetime.fromisoformat(
                        published_at.replace("Z", "+00:00")
                    )
                    if pub.replace(tzinfo=None) < cutoff:
                        continue
                except (ValueError, TypeError):
                    pass

            duration = None
            if hasattr(entry, "itunes_duration"):
                duration = self._parse_duration(entry.itunes_duration)

            item = self.make_content_item(
                module=self.module,
                content_type="podcast",
                title=title.strip(),
                url=link.strip(),
                source=podcast["name"],
                platform="podcast",
                category="podcast",
                summary=summary,
                creator_name=podcast["name"],
                duration_seconds=duration,
                published_at=published_at,
            )
            item["relevance_score"] = self._calculate_relevance(item)
            items.append(item)

        return items

    @staticmethod
    def fetch_transcript(video_id: str, language: str = "en") -> str:
        if not HAS_TRANSCRIPT_API:
            return ""
        try:
            lang_codes = [language, "en", "zh-Hans", "zh-Hant", "zh"]
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            transcript = None
            for code in lang_codes:
                try:
                    transcript = transcript_list.find_transcript([code])
                    break
                except Exception:
                    continue

            if transcript is None:
                try:
                    generated = transcript_list.find_generated_transcript(
                        lang_codes
                    )
                    transcript = generated
                except Exception:
                    return ""

            if transcript is None:
                return ""

            entries = transcript.fetch()
            text_parts = [entry["text"] for entry in entries]
            return " ".join(text_parts)
        except Exception:
            return ""

    @staticmethod
    def _extract_video_id(url: str) -> str:
        patterns = [
            r"(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})",
            r"(?:embed/)([a-zA-Z0-9_-]{11})",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return ""

    def _calculate_relevance(self, item: dict) -> float:
        text = f"{item['title']} {item['summary']}".lower()
        score = 0.0

        high = self.keywords.get("high_relevance", [])
        high_hits = sum(1 for kw in high if kw.lower() in text)
        score += min(high_hits * 0.3, 0.6)

        medium = self.keywords.get("medium_relevance", [])
        medium_hits = sum(1 for kw in medium if kw.lower() in text)
        score += min(medium_hits * 0.1, 0.3)

        low = self.keywords.get("low_relevance", [])
        low_hits = sum(1 for kw in low if kw.lower() in text)
        score += min(low_hits * 0.05, 0.1)

        # 所有博主内容基础分 0.4 （因为都是精选频道）
        score = max(score, 0.4)

        return min(score, 1.0)

    @staticmethod
    def _parse_duration(duration_str: str) -> Optional[int]:
        if not duration_str:
            return None
        try:
            parts = str(duration_str).split(":")
            if len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            elif len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            else:
                return int(parts[0])
        except (ValueError, TypeError):
            return None
