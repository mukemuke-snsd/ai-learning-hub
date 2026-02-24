"""内容处理器 - 过滤、评分、AI 富化"""

import json
import logging
from typing import Optional

from config.loader import load_settings
from tracker.database import Database

log = logging.getLogger(__name__)


class ContentProcessor:
    """内容处理和过滤，支持多模块 + AI 富化"""

    def __init__(self, db: Optional[Database] = None, module: str = "geo"):
        self.settings = load_settings()
        self.db = db or Database()
        self.module = module
        proc_cfg = self.settings.get("processor", {})
        self.min_score = proc_cfg.get("min_relevance_score", 0.3)
        self.max_daily = proc_cfg.get("max_daily_articles", 15)

    def process_and_save(self, items: list) -> dict:
        stats = {
            "total_fetched": len(items),
            "new_saved": 0,
            "duplicates": 0,
            "low_relevance": 0,
        }
        items = self._dedup_by_title(items)
        for item in items:
            if item.get("relevance_score", 0) < self.min_score:
                stats["low_relevance"] += 1
                continue
            is_new = self.db.save_content_item(item)
            if is_new:
                stats["new_saved"] += 1
            else:
                stats["duplicates"] += 1
        return stats

    @staticmethod
    def _normalize_title(title: str) -> str:
        """将标题归一化用于去重比较"""
        import re
        t = title.lower().strip()
        t = re.sub(r'[^\w\s]', '', t)
        t = re.sub(r'\s+', ' ', t)
        return t

    def _dedup_by_title(self, items: list) -> list:
        """批内标题去重：相似标题只保留相关度最高的一条"""
        seen = {}
        for item in items:
            norm = self._normalize_title(item.get("title", ""))
            if not norm or len(norm) < 10:
                key = item.get("url", id(item))
            else:
                key = norm[:60]
            existing = seen.get(key)
            if existing is None:
                seen[key] = item
            else:
                if item.get("relevance_score", 0) > existing.get("relevance_score", 0):
                    seen[key] = item
        deduped = list(seen.values())
        removed = len(items) - len(deduped)
        if removed > 0:
            log.info("标题去重: 移除 %d 条重复内容", removed)
        return deduped

    def get_daily_articles(self) -> list:
        return self.db.get_unused_content(
            module=self.module,
            limit=self.max_daily,
            min_score=self.min_score,
        )

    def get_articles_for_period(self, start_date: str,
                                end_date: str) -> list:
        return self.db.get_content_by_date_range(
            start_date, end_date, self.module
        )

    def enrich_with_ai(self, items: list = None) -> int:
        """AI enrichment: generate core_conclusion, actionable_insight,
        ai_quality_score for unenriched items.
        Returns number of items enriched."""
        from generators.ai_engine import AIEngine

        if items is None:
            items = self.db.get_unenriched_content(limit=20)

        if not items:
            return 0

        ai = AIEngine()
        enriched = 0

        for item in items:
            title = item.get("title", "")
            summary = item.get("summary", "")[:500]
            source = item.get("source", "")
            module = item.get("module", "")

            prompt = (
                f"请分析以下内容并返回 JSON：\n\n"
                f"标题: {title}\n来源: {source}\n模块: {module}\n"
                f"摘要: {summary}\n\n"
                f"返回格式（严格 JSON，不要多余文字）：\n"
                f'{{"core_conclusion": "一句话核心结论",'
                f' "actionable_insight": "一句话可落地启发（结合产品/策略角度）",'
                f' "ai_quality_score": 5,'
                f' "tags": "标签1, 标签2"}}\n\n'
                f"ai_quality_score 评分标准（0-10）：\n"
                f"- 8-10: 突破性发现或高度可落地\n"
                f"- 5-7: 有价值的信息或洞察\n"
                f"- 3-4: 一般性信息\n"
                f"- 0-2: 低价值或重复内容"
            )

            try:
                result = ai.generate_json(
                    system_prompt="你是一位 AI 内容分析师，擅长快速评估内容价值。只返回 JSON。",
                    user_prompt=prompt,
                )

                if "error" not in result:
                    self.db.update_enrichment(
                        item_id=item["id"],
                        core_conclusion=result.get("core_conclusion", ""),
                        actionable_insight=result.get("actionable_insight", ""),
                        ai_quality_score=float(result.get("ai_quality_score", 5)),
                    )
                    if result.get("tags"):
                        ph = "%s" if self.db.use_postgres else "?"
                        self.db._execute(
                            f"UPDATE content_items SET tags = {ph} WHERE id = {ph}",
                            (result["tags"], item["id"])
                        )
                        self.db.conn.commit()
                    enriched += 1
                else:
                    log.warning("Enrich failed for %s: %s", title[:40], result["error"])
            except Exception as e:
                log.warning("Enrich exception for %s: %s", title[:40], str(e)[:80])

        return enriched
