"""arXiv 论文抓取器 - 支持多模块（ai_tech / geo）"""

import time
from datetime import datetime
from typing import Optional

from config.loader import load_module_config, load_settings
from scrapers.base_scraper import BaseScraper

try:
    import arxiv
    HAS_ARXIV = True
except ImportError:
    HAS_ARXIV = False


class ArxivScraper(BaseScraper):
    """arXiv 论文抓取器，支持 module 参数加载不同关键词"""

    def __init__(self, module: str = "ai_tech"):
        self.module = module
        self.module_cfg = load_module_config(module)
        settings = load_settings()
        scraper_cfg = settings.get("scraper", {})

        self.categories = self.module_cfg.get("arxiv_categories", ["cs.AI"])
        self.arxiv_settings = self.module_cfg.get("arxiv_settings", {})
        self.keywords = self.module_cfg.get("keywords", {})
        self.max_results = self.arxiv_settings.get("max_results_per_query", 20)
        self.delay = scraper_cfg.get("request_delay", 1)

    def fetch_all(self, verbose: bool = True) -> list:
        if not HAS_ARXIV:
            if verbose:
                print("  ⚠️  arxiv 包未安装，跳过论文抓取")
            return []

        all_papers = []

        high_kw = self.keywords.get("high_relevance", [])
        search_queries = high_kw[:3]

        for query in search_queries:
            if verbose:
                print(f"  📄 搜索 arXiv: '{query}'...")
            try:
                papers = self._search(query)
                all_papers.extend(papers)
                if verbose:
                    print(f"     ✅ 获取 {len(papers)} 篇论文")
            except Exception as e:
                if verbose:
                    print(f"     ❌ 失败: {str(e)[:80]}")
            time.sleep(self.delay * 2)

        for cat in self.categories[:3]:
            if verbose:
                print(f"  📄 浏览分类: {cat}...")
            try:
                papers = self._browse_category(cat)
                all_papers.extend(papers)
                if verbose:
                    print(f"     ✅ 获取 {len(papers)} 篇论文")
            except Exception as e:
                if verbose:
                    print(f"     ❌ 失败: {str(e)[:80]}")
            time.sleep(self.delay * 2)

        seen_urls = set()
        unique = []
        for p in all_papers:
            if p["url"] not in seen_urls:
                seen_urls.add(p["url"])
                unique.append(p)

        return unique

    def _search(self, query: str) -> list:
        client = arxiv.Client()
        search = arxiv.Search(
            query=query,
            max_results=self.max_results,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending,
        )

        papers = []
        for result in client.results(search):
            paper = self._parse_result(result)
            if paper:
                papers.append(paper)

        return papers

    def _browse_category(self, category: str) -> list:
        client = arxiv.Client()
        search = arxiv.Search(
            query=f"cat:{category}",
            max_results=10,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending,
        )

        papers = []
        for result in client.results(search):
            paper = self._parse_result(result)
            if paper:
                papers.append(paper)

        return papers

    def _parse_result(self, result) -> Optional[dict]:
        title = result.title or ""
        url = result.entry_id or ""
        if not title or not url:
            return None

        authors = ", ".join(a.name for a in (result.authors or [])[:5])
        categories = ", ".join(result.categories or [])
        summary = (result.summary or "")[:800]
        published_at = ""
        if result.published:
            published_at = result.published.isoformat()

        item = self.make_content_item(
            module=self.module,
            content_type="paper",
            title=title.strip(),
            url=url.strip(),
            source="arXiv",
            platform="arxiv",
            category=categories,
            summary=summary,
            creator_name=authors,
            published_at=published_at,
            tags=categories,
        )

        item["relevance_score"] = self._calculate_relevance(item)
        return item

    def _calculate_relevance(self, paper: dict) -> float:
        text = f"{paper['title']} {paper['summary']}".lower()
        score = 0.0

        high = self.keywords.get("high_relevance", [])
        high_hits = sum(1 for kw in high if kw.lower() in text)
        score += min(high_hits * 0.25, 0.6)

        medium = self.keywords.get("medium_relevance", [])
        medium_hits = sum(1 for kw in medium if kw.lower() in text)
        score += min(medium_hits * 0.1, 0.3)

        low = self.keywords.get("low_relevance", [])
        low_hits = sum(1 for kw in low if kw.lower() in text)
        score += min(low_hits * 0.05, 0.1)

        return min(score, 1.0)
