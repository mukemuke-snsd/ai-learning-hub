#!/usr/bin/env python3
"""
每日自动任务 - 适用于 cron / launchd 定时执行
================================================
流程：抓取三模块 → AI 富化 → 生成统一跨模块早报

用法:
    python3 auto_daily.py           # 自动判断工作日/周末
    python3 auto_daily.py geo       # 只抓取指定模块（不生成统一早报）
    python3 auto_daily.py --weekly  # 强制包含中频源
"""

import sys
import logging
from pathlib import Path
from datetime import datetime, date

sys.path.insert(0, str(Path(__file__).parent))

LOG_FILE = Path(__file__).parent / "data" / "auto_daily.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("auto_daily")

ALL_MODULES = ["geo", "ai_tech", "ai_product"]


def _log_health(module: str, rss_scraper):
    """输出 RSS 源健康检查报告"""
    health = rss_scraper.get_health_report()
    ok_count = len(health["ok"])
    fail_list = health["fail"]
    if fail_list:
        log.warning(
            "[%s] 源健康检查: %d 成功, %d 失败 ⚠️",
            module, ok_count, len(fail_list),
        )
        for name, err in fail_list:
            log.warning("[%s]   ❌ %s — %s", module, name, err)
    else:
        log.info("[%s] 源健康检查: %d/%d 全部成功 ✅", module, ok_count, ok_count)


def fetch_module(db, module: str, include_weekly: bool = False):
    """抓取指定模块的最新内容"""
    from scrapers.rss_scraper import RSSScraper
    from processors.content_processor import ContentProcessor

    if module == "ai_product":
        items = []
        try:
            from scrapers.youtube_scraper import YouTubeScraper
            scraper = YouTubeScraper(fetch_transcripts=False)
            items.extend(scraper.fetch_all(verbose=False))
        except ImportError:
            log.warning("[ai_product] youtube_transcript_api 未安装，跳过 YouTube")

        rss = RSSScraper(module=module)
        rss_items = rss.fetch_all(verbose=False)
        items.extend(rss_items)
        log.info("[ai_product] RSS 获取 %d 条内容", len(rss_items))
        _log_health(module, rss)

        processor = ContentProcessor(db, module=module)
        return processor.process_and_save(items)

    if module == "ai_tech":
        items = []
        try:
            from scrapers.arxiv_scraper import ArxivScraper
            scraper = ArxivScraper(module="ai_tech")
            items = scraper.fetch_all(verbose=False)
        except ImportError:
            log.warning("[ai_tech] arxiv 包未安装，跳过 arXiv")

        try:
            from scrapers.youtube_scraper import YouTubeScraper
            yt = YouTubeScraper(module="ai_tech", fetch_transcripts=False)
            yt_items = yt.fetch_all(verbose=False)
            items.extend(yt_items)
            log.info("[ai_tech] YouTube 获取 %d 条内容", len(yt_items))
        except ImportError:
            log.warning("[ai_tech] youtube_transcript_api 未安装，跳过 YouTube")

        rss = RSSScraper(module=module)
        items.extend(rss.fetch_all(verbose=False))
        _log_health(module, rss)
        processor = ContentProcessor(db, module=module)
        return processor.process_and_save(items)

    # GEO: 分层抓取（纯 RSS，arXiv 已移至 ai_tech）
    scraper = RSSScraper(module=module)
    log.info("[%s] 抓取高频源 (daily)...", module)
    items = scraper.fetch_all(verbose=False, frequency="daily")

    if include_weekly:
        log.info("[%s] 抓取中频源 (weekly)...", module)
        items.extend(scraper.fetch_all(verbose=False, frequency="weekly"))

    _log_health(module, scraper)
    processor = ContentProcessor(db, module=module)
    return processor.process_and_save(items)


def enrich_all(db):
    """AI 富化所有未处理的内容"""
    from processors.content_processor import ContentProcessor
    processor = ContentProcessor(db)
    unenriched = db.get_unenriched_content(limit=20)
    if unenriched:
        log.info("AI 富化 %d 条新内容...", len(unenriched))
        count = processor.enrich_with_ai(unenriched)
        log.info("已富化 %d 条 ✅", count)
    else:
        log.info("无需富化的新内容")


def generate_unified_briefing(db, today_str: str):
    """生成统一跨模块早报"""
    from generators.daily_briefing import DailyBriefingGenerator

    existing = db.get_briefing(today_str, module="unified")
    if existing:
        log.info("今日统一早报已存在，跳过")
        return

    log.info("生成统一跨模块早报...")
    generator = DailyBriefingGenerator(db, module="geo")
    generator.generate_unified(today_str)
    log.info("统一早报生成完成 ✅")


def run(modules: list, force_weekly: bool = False):
    from config.loader import load_settings
    from tracker.database import Database

    log.info("=" * 50)
    log.info("🌅 每日自动任务启动 — %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    is_weekend = date.today().weekday() >= 5
    include_weekly = force_weekly or is_weekend

    if include_weekly:
        log.info("📊 包含中频源抓取（周末 / --weekly）")
    else:
        log.info("📅 仅抓取高频源（工作日）")

    settings = load_settings()
    if not settings["openai"]["api_key"]:
        log.error("❌ OPENAI_API_KEY 未设置，无法生成简报")
        return

    db = Database()
    today_str = date.today().isoformat()

    # Step 1: 抓取所有模块
    for module in modules:
        log.info("-" * 30)
        log.info("[%s] 开始抓取", module)
        try:
            stats = fetch_module(db, module, include_weekly=include_weekly)
            log.info(
                "[%s] 抓取完成: 新内容 %d / 总共 %d / 重复 %d / 低相关 %d",
                module, stats["new_saved"], stats["total_fetched"],
                stats["duplicates"], stats["low_relevance"],
            )
        except Exception:
            log.exception("[%s] 抓取失败", module)

    # Step 2: AI 富化
    try:
        enrich_all(db)
    except Exception:
        log.exception("AI 富化失败")

    # Step 3: 生成统一早报
    if len(modules) == len(ALL_MODULES):
        try:
            generate_unified_briefing(db, today_str)
        except Exception:
            log.exception("统一早报生成失败")

    db.close()
    log.info("🎉 每日自动任务完成！")
    log.info("=" * 50)


if __name__ == "__main__":
    target_modules = ALL_MODULES
    force_weekly = "--weekly" in sys.argv

    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if args and args[0] in ALL_MODULES:
        target_modules = [args[0]]

    run(target_modules, force_weekly=force_weekly)
