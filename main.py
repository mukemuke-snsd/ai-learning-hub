#!/usr/bin/env python3
"""
AI Learning Hub - 统一 AI 学习助手
===================================
用法:
    python main.py daily [module]    每日学习流程（抓取→简报→测验）
    python main.py fetch [module]    抓取最新内容
    python main.py briefing [module] 生成今日简报
    python main.py quiz [module]     生成并进行测验
    python main.py weekly            生成跨模块周度总结
    python main.py monthly           生成跨模块月度总结
    python main.py progress          查看学习进度
    python main.py search <关键词>   搜索知识库

模块: product_radar / research_lab (默认 product_radar)
"""

import sys
import json
from datetime import date

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from config.loader import load_settings
from scrapers.rss_scraper import RSSScraper
from processors.content_processor import ContentProcessor
from generators.daily_briefing import DailyBriefingGenerator
from generators.quiz_generator import QuizGenerator
from generators.summary_generator import SummaryGenerator
from tracker.database import Database
from tracker.progress import ProgressTracker

console = Console()

MODULE_NAMES = {
    "product_radar": "产品雷达",
    "research_lab": "研究前沿",
}


def get_module(args: list) -> str:
    for a in args:
        if a in MODULE_NAMES:
            return a
    return "product_radar"


def cmd_fetch(db: Database, module: str):
    name = MODULE_NAMES.get(module, module)
    console.print(f"\n[bold cyan]📡 开始抓取 {name} 资讯...[/bold cyan]\n")

    items = []

    if module == "research_lab":
        try:
            from scrapers.arxiv_scraper import ArxivScraper
            scraper = ArxivScraper(module=module)
            arxiv_items = scraper.fetch_all(verbose=True)
            items.extend(arxiv_items)
        except ImportError:
            console.print("[yellow]arxiv 包未安装，跳过 arXiv[/yellow]")

    try:
        from scrapers.youtube_scraper import YouTubeScraper
        yt = YouTubeScraper(module=module, fetch_transcripts=False)
        items.extend(yt.fetch_all(verbose=True))
    except ImportError:
        console.print("[yellow]youtube_transcript_api 未安装，跳过 YouTube[/yellow]")

    rss = RSSScraper(module=module)
    items.extend(rss.fetch_all(verbose=True))

    processor = ContentProcessor(db, module=module)
    stats = processor.process_and_save(items)
    _print_stats(stats)
    return stats


def _print_stats(stats: dict):
    console.print(f"\n[bold green]✅ 抓取完成![/bold green]")
    console.print(f"  📊 总抓取: {stats['total_fetched']} 篇")
    console.print(f"  🆕 新内容: {stats['new_saved']} 篇")
    console.print(f"  🔄 重复: {stats['duplicates']} 篇")
    console.print(f"  📉 低相关: {stats['low_relevance']} 篇\n")


def cmd_briefing(db: Database, module: str):
    name = MODULE_NAMES.get(module, module)
    console.print(f"\n[bold cyan]📰 生成今日 {name} 学习简报...[/bold cyan]\n")

    processor = ContentProcessor(db, module=module)
    articles = processor.get_daily_articles()
    generator = DailyBriefingGenerator(db, module=module)

    if articles:
        console.print(f"  📚 选取 {len(articles)} 篇高相关内容")
        briefing = generator.generate(articles)
    else:
        console.print("  ⚠️  今日没有新内容，生成主题学习材料...")
        briefing = generator.generate_no_articles()

    console.print()
    console.print(Markdown(briefing))
    db.log_activity("briefing_read", 30,
                    f"阅读 {date.today()} {name} 简报", module)
    console.print(
        f"\n[bold green]✅ 简报已保存[/bold green]\n"
    )
    return briefing


def cmd_quiz(db: Database, module: str, review: bool = False):
    today_str = date.today().isoformat()
    quiz_gen = QuizGenerator(db, module=module)

    if review:
        record = db.get_quiz(today_str, module=module)
        if not record:
            console.print("[yellow]今日还没有生成测验[/yellow]")
            return
        quiz_data = json.loads(record["questions"])
        console.print(Markdown(quiz_gen.format_answers_for_display(quiz_data)))
        return

    briefing = db.get_briefing(today_str, module=module)
    if not briefing:
        console.print("[yellow]今日还没有生成简报，先生成...[/yellow]\n")
        cmd_briefing(db, module)
        briefing = db.get_briefing(today_str, module=module)

    if not briefing:
        console.print("[red]无法获取简报内容[/red]")
        return

    name = MODULE_NAMES.get(module, module)
    console.print(f"\n[bold cyan]📝 生成 {name} 测验...[/bold cyan]\n")
    quiz_data = quiz_gen.generate_quiz(briefing["content"], today_str)

    if "error" in quiz_data:
        console.print(f"[red]测验生成失败: {quiz_data['error']}[/red]")
        return

    console.print(Markdown(quiz_gen.format_quiz_for_display(quiz_data)))

    if Confirm.ask("\n准备好答题了吗？"):
        user_answers = {}
        for q in quiz_data.get("questions", []):
            q_id = str(q.get("id", ""))
            q_type = q.get("type", "unknown")
            console.print(f"\n[bold]第 {q_id} 题: {q['question']}[/bold]")

            if q_type == "multiple_choice":
                for opt in q.get("options", []):
                    console.print(f"  {opt}")
                answer = Prompt.ask("你的答案 (A/B/C/D)")
            elif q_type == "true_false":
                answer = Prompt.ask("你的答案 (A=正确/B=错误)")
            elif q_type == "short_answer":
                answer = Prompt.ask("请输入你的答案")
            else:
                answer = Prompt.ask("你的答案")
            user_answers[q_id] = answer

        console.print("\n[bold cyan]🔍 评估中...[/bold cyan]\n")
        evaluation = quiz_gen.evaluate_answers(quiz_data, user_answers)

        console.print(Panel(
            f"[bold]{evaluation['summary']}[/bold]",
            title="📊 测验结果",
            border_style="green" if evaluation["passed"] else "red",
        ))
        for r in evaluation.get("results", []):
            console.print(f"\n第 {r['question_id']} 题: {r['feedback']}")

        db.log_activity("quiz_completed", 15,
                        f"测验分数: {evaluation['percentage']:.1f}%",
                        module)


def cmd_weekly(db: Database):
    console.print("\n[bold cyan]📊 生成跨模块周度总结...[/bold cyan]\n")
    gen = SummaryGenerator(db)
    report = gen.generate_weekly()
    console.print(Markdown(report))
    db.log_activity("weekly_review", 15,
                    f"完成第{date.today().isocalendar()[1]}周总结")


def cmd_monthly(db: Database):
    console.print("\n[bold cyan]📅 生成跨模块月度总结...[/bold cyan]\n")
    gen = SummaryGenerator(db)
    report = gen.generate_monthly()
    console.print(Markdown(report))
    db.log_activity("monthly_review", 30,
                    f"完成{date.today().year}年{date.today().month}月总结")


def cmd_progress(db: Database):
    tracker = ProgressTracker(db)
    overview = tracker.get_overview()
    console.print(Markdown(overview))
    streak = tracker.get_streak()
    console.print(f"\n🔥 当前连续学习: {streak['current_streak']} 天")
    console.print(f"📅 累计活跃天数: {streak['total_active_days']} 天\n")


def cmd_search(db: Database, keyword: str):
    console.print(f"\n[bold cyan]🔍 搜索知识库: '{keyword}'...[/bold cyan]\n")
    results = db.search_knowledge(keyword)
    if results:
        for item in results:
            mod = {"product_radar": "产品雷达", "research_lab": "研究前沿",
                   "geo": "GEO", "ai_tech": "AI技术",
                   "ai_product": "AI产品"}.get(item.get("module", ""), "")
            console.print(Panel(
                f"**[{mod}] {item['topic']}** [{item.get('category', '')}]\n\n"
                f"{item['content'][:300]}...\n\n"
                f"标签: {item.get('tags', '')}",
                border_style="blue",
            ))
    else:
        console.print("[yellow]未找到相关内容[/yellow]")


def cmd_daily(db: Database, module: str):
    name = MODULE_NAMES.get(module, module)
    console.print(Panel(
        f"[bold]🌅 {name} 每日学习流程[/bold]\n\n"
        f"Step 1: 📡 抓取最新内容\n"
        f"Step 2: 📰 生成学习简报\n"
        f"Step 3: 📝 学习测验",
        title="AI Learning Hub",
        border_style="cyan",
    ))

    cmd_fetch(db, module)
    cmd_briefing(db, module)

    console.print()
    if Confirm.ask("📝 准备开始测验？"):
        cmd_quiz(db, module)

    if date.today().weekday() == 4:
        console.print("[bold yellow]📊 今天是周五，建议生成周度总结！[/bold yellow]")
        if Confirm.ask("是否生成周度总结？"):
            cmd_weekly(db)

    console.print(Panel(
        "[bold green]🎉 今日学习流程完成！[/bold green]\n"
        "用 'python main.py progress' 查看学习进度",
        border_style="green",
    ))


def main():
    if len(sys.argv) < 2:
        console.print(Panel(
            "[bold]AI Learning Hub[/bold] — 统一 AI 学习助手\n\n"
            "用法:\n"
            "  [cyan]python main.py daily [module][/cyan]     每日学习流程\n"
            "  [cyan]python main.py fetch [module][/cyan]     抓取最新内容\n"
            "  [cyan]python main.py briefing [module][/cyan]  生成今日简报\n"
            "  [cyan]python main.py quiz [module][/cyan]      今日测验\n"
            "  [cyan]python main.py weekly[/cyan]             跨模块周度总结\n"
            "  [cyan]python main.py monthly[/cyan]            跨模块月度总结\n"
            "  [cyan]python main.py progress[/cyan]           学习进度\n"
            "  [cyan]python main.py search <关键词>[/cyan]    搜索知识库\n\n"
            "模块: product_radar / research_lab (默认 product_radar)",
            title="📚 使用帮助",
            border_style="blue",
        ))
        return

    command = sys.argv[1].lower()
    module = get_module(sys.argv[2:])

    settings = load_settings()
    if not settings["openai"]["api_key"] and command not in (
        "fetch", "progress"
    ):
        console.print(
            "[bold red]❌ 未设置 OPENAI_API_KEY[/bold red]\n"
            "请运行: export OPENAI_API_KEY='your-api-key'\n"
        )
        return

    db = Database()

    try:
        if command == "daily":
            cmd_daily(db, module)
        elif command == "fetch":
            cmd_fetch(db, module)
        elif command == "briefing":
            cmd_briefing(db, module)
        elif command == "quiz":
            review = "--review" in sys.argv
            cmd_quiz(db, module, review=review)
        elif command == "weekly":
            cmd_weekly(db)
        elif command == "monthly":
            cmd_monthly(db)
        elif command == "progress":
            cmd_progress(db)
        elif command == "search":
            if len(sys.argv) < 3:
                console.print("[yellow]请提供搜索关键词[/yellow]")
            else:
                cmd_search(db, sys.argv[2])
        else:
            console.print(f"[red]未知命令: {command}[/red]")
    finally:
        db.close()


if __name__ == "__main__":
    main()
