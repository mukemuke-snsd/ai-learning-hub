"""X/Twitter 抓取器 - 通过 RSSHub 将 Twitter 转为 RSS"""

import re
import time
from datetime import datetime, timedelta
from typing import Optional

import feedparser
import requests
from bs4 import BeautifulSoup

from config.loader import load_module_config, load_settings
from scrapers.base_scraper import BaseScraper


class TwitterScraper(BaseScraper):
    """通过 RSSHub 抓取 X/Twitter 账号内容"""

    def __init__(self):
        self.module_cfg = load_module_config("product_radar")
        settings = load_settings()
        scraper_cfg = settings.get("scraper", {})

        twitter_cfg = self.module_cfg.get("twitter_accounts", {})
        self.rsshub_base = twitter_cfg.get("rsshub_base", "https://rsshub.app")
        self.accounts = twitter_cfg.get("accounts", [])
        self.keywords_filter = [
            kw.lower() for kw in twitter_cfg.get("keywords_filter", [])
        ]

        self.timeout = scraper_cfg.get("request_timeout", 15)
        self.delay = scraper_cfg.get("request_delay", 1)
        self.max_age_days = scraper_cfg.get("max_article_age_days", 3)
        self.user_agent = scraper_cfg.get("user_agent", "AI-Learning-Hub/1.0")

    def fetch_all(self, verbose: bool = True) -> list:
        all_tweets = []

        for account in self.accounts:
            username = account.get("username", "")
            name = account.get("name", username)
            if not username:
                continue

            if verbose:
                print(f"  🐦 抓取 X/@{username} ({name})...")

            try:
                tweets = self._fetch_account(account)
                all_tweets.extend(tweets)
                if verbose:
                    print(f"     ✅ 获取 {len(tweets)} 条相关推文")
            except Exception as e:
                if verbose:
                    print(f"     ❌ 失败: {str(e)[:80]}")

            time.sleep(self.delay)

        return all_tweets

    def _fetch_account(self, account: dict) -> list:
        username = account["username"]
        rss_url = f"{self.rsshub_base}/twitter/user/{username}"

        headers = {"User-Agent": self.user_agent}
        response = requests.get(rss_url, headers=headers, timeout=self.timeout)
        response.raise_for_status()

        feed = feedparser.parse(response.content)
        cutoff = datetime.now() - timedelta(days=self.max_age_days)

        tweets = []
        for entry in feed.entries[:20]:
            tweet = self._parse_entry(entry, account)
            if tweet is None:
                continue

            if tweet["published_at"]:
                try:
                    pub = datetime.fromisoformat(
                        tweet["published_at"].replace("Z", "+00:00")
                    )
                    if pub.replace(tzinfo=None) < cutoff:
                        continue
                except (ValueError, TypeError):
                    pass

            if not self._matches_keywords(tweet):
                continue

            tweet["relevance_score"] = self._calculate_relevance(tweet)
            tweets.append(tweet)

        return tweets

    def _parse_entry(self, entry, account: dict) -> Optional[dict]:
        title = getattr(entry, "title", "")
        link = getattr(entry, "link", "")
        if not link:
            return None

        text = ""
        if hasattr(entry, "summary"):
            text = BeautifulSoup(
                entry.summary, "html.parser"
            ).get_text(strip=True)[:500]
        elif hasattr(entry, "description"):
            text = BeautifulSoup(
                entry.description, "html.parser"
            ).get_text(strip=True)[:500]

        if not title:
            title = text[:100] + ("..." if len(text) > 100 else "")

        published_at = ""
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                published_at = datetime(
                    *entry.published_parsed[:6]
                ).isoformat()
            except (TypeError, ValueError):
                pass

        return self.make_content_item(
            module="product_radar",
            content_type="note",
            title=title.strip(),
            url=link.strip(),
            source=f"X/@{account['username']}",
            platform="twitter",
            category="twitter",
            summary=text,
            content=text,
            creator_name=account.get("name", account["username"]),
            published_at=published_at,
            tags="Twitter, AI",
        )

    def _matches_keywords(self, tweet: dict) -> bool:
        text = f"{tweet['title']} {tweet['summary']}".lower()
        return any(kw in text for kw in self.keywords_filter)

    def _calculate_relevance(self, tweet: dict) -> float:
        text = f"{tweet['title']} {tweet['summary']}".lower()

        score = 0.3
        keywords = self.module_cfg.get("keywords", {})

        high = keywords.get("high_relevance", [])
        high_hits = sum(1 for kw in high if kw.lower() in text)
        score += min(high_hits * 0.2, 0.4)

        medium = keywords.get("medium_relevance", [])
        medium_hits = sum(1 for kw in medium if kw.lower() in text)
        score += min(medium_hits * 0.1, 0.2)

        return min(score, 1.0)
