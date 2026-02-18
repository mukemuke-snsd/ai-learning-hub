"""RSS 信息源抓取器 - 通用版，支持多模块"""

import time
from datetime import datetime, timedelta
from typing import Optional

import feedparser
import requests
from bs4 import BeautifulSoup

from config.loader import load_module_config, load_settings
from scrapers.base_scraper import BaseScraper


class RSSScraper(BaseScraper):
    """通用 RSS 抓取器，支持任意模块的 RSS 源"""

    def __init__(self, module: str = "geo"):
        self.module = module
        module_cfg = load_module_config(module)
        settings = load_settings()

        self.feeds = module_cfg.get("rss_feeds", [])
        self.keywords = module_cfg.get("keywords", {})
        scraper_cfg = settings.get("scraper", {})

        self.timeout = scraper_cfg.get("request_timeout", 15)
        self.delay = scraper_cfg.get("request_delay", 1)
        self.max_age_days = scraper_cfg.get("max_article_age_days", 3)
        self.max_per_source = scraper_cfg.get("max_articles_per_source", 20)
        self.user_agent = scraper_cfg.get("user_agent", "AI-Learning-Hub/1.0")

    def fetch_all(self, verbose: bool = True,
                  frequency: str = None) -> list:
        """抓取所有 RSS 源。frequency 可选 'daily'/'weekly'/'monthly'，
        为 None 时抓取所有源。"""
        all_articles = []
        for feed_config in self.feeds:
            if frequency and feed_config.get("frequency", "daily") != frequency:
                continue
            if verbose:
                freq_tag = feed_config.get("frequency", "daily")
                print(f"  📡 [{freq_tag}] 抓取: {feed_config['name']}...")
            try:
                articles = self._fetch_feed(feed_config)
                all_articles.extend(articles)
                if verbose:
                    print(f"     ✅ 获取 {len(articles)} 篇文章")
            except Exception as e:
                if verbose:
                    print(f"     ❌ 失败: {str(e)[:80]}")
            time.sleep(self.delay)
        return all_articles

    def get_feeds_by_frequency(self) -> dict:
        """按频率分组返回信息源列表"""
        groups = {"daily": [], "weekly": [], "monthly": []}
        for feed in self.feeds:
            freq = feed.get("frequency", "daily")
            groups.setdefault(freq, []).append(feed)
        return groups

    def _fetch_feed(self, feed_config: dict) -> list:
        headers = {"User-Agent": self.user_agent}
        try:
            response = requests.get(
                feed_config["url"], headers=headers, timeout=self.timeout
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise Exception(f"HTTP 请求失败: {e}")

        feed = feedparser.parse(response.content)
        articles = []
        cutoff_date = datetime.now() - timedelta(days=self.max_age_days)

        for entry in feed.entries[:self.max_per_source]:
            article = self._parse_entry(entry, feed_config)
            if article is None:
                continue

            if article["published_at"]:
                try:
                    pub_date = datetime.fromisoformat(
                        article["published_at"].replace("Z", "+00:00")
                    )
                    if pub_date.replace(tzinfo=None) < cutoff_date:
                        continue
                except (ValueError, TypeError):
                    pass

            article["relevance_score"] = self._calculate_relevance(article)
            articles.append(article)

        return articles

    def _parse_entry(self, entry, feed_config: dict) -> Optional[dict]:
        title = getattr(entry, "title", "")
        link = getattr(entry, "link", "")
        if not title or not link:
            return None

        summary = ""
        if hasattr(entry, "summary"):
            summary = BeautifulSoup(
                entry.summary, "html.parser"
            ).get_text(strip=True)[:500]
        elif hasattr(entry, "description"):
            summary = BeautifulSoup(
                entry.description, "html.parser"
            ).get_text(strip=True)[:500]

        published_at = ""
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                published_at = datetime(
                    *entry.published_parsed[:6]
                ).isoformat()
            except (TypeError, ValueError):
                pass
        elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
            try:
                published_at = datetime(
                    *entry.updated_parsed[:6]
                ).isoformat()
            except (TypeError, ValueError):
                pass

        content_type = "paper" if self.module == "ai_papers" else "article"

        return self.make_content_item(
            module=self.module,
            content_type=content_type,
            title=title.strip(),
            url=link.strip(),
            source=feed_config["name"],
            platform="rss",
            category=feed_config.get("category", ""),
            summary=summary,
            published_at=published_at,
        )

    def _calculate_relevance(self, article: dict) -> float:
        text = f"{article['title']} {article['summary']}".lower()
        score = 0.0

        high_keywords = self.keywords.get("high_relevance", [])
        high_hits = sum(1 for kw in high_keywords if kw.lower() in text)
        score += min(high_hits * 0.3, 0.6)

        medium_keywords = self.keywords.get("medium_relevance", [])
        medium_hits = sum(1 for kw in medium_keywords if kw.lower() in text)
        score += min(medium_hits * 0.1, 0.3)

        low_keywords = self.keywords.get("low_relevance", [])
        low_hits = sum(1 for kw in low_keywords if kw.lower() in text)
        score += min(low_hits * 0.05, 0.1)

        if article.get("category") in (
            "geo_core", "ai_search", "official", "papers", "ai_research"
        ):
            score += 0.1

        return min(score, 1.0)

    def fetch_article_content(self, url: str) -> str:
        headers = {"User-Agent": self.user_agent}
        try:
            response = requests.get(
                url, headers=headers, timeout=self.timeout
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            article_body = (
                soup.find("article")
                or soup.find("div", class_="post-content")
                or soup.find("div", class_="entry-content")
                or soup.find("main")
            )
            if article_body:
                text = article_body.get_text(separator="\n", strip=True)
            else:
                text = soup.get_text(separator="\n", strip=True)
            lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
            return "\n".join(lines)[:3000]
        except Exception:
            return ""


# 兼容旧名称
RSSCraper = RSSScraper
