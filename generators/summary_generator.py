"""周度/月度总结生成器 - 多模块支持"""

from datetime import date, datetime, timedelta

from config.loader import (
    load_settings, load_module_config, load_all_module_configs, get_data_path
)
from generators.ai_engine import AIEngine
from tracker.database import Database


class SummaryGenerator:
    """周度和月度总结生成器，支持跨模块"""

    def __init__(self, db: Database = None):
        self.db = db or Database()
        self.ai = AIEngine()
        self.settings = load_settings()
        self.all_modules = load_all_module_configs()

    def generate_weekly(self, target_date: date = None,
                        module: str = "all") -> str:
        if not target_date:
            target_date = date.today()

        weekday = target_date.weekday()
        start_of_week = target_date - timedelta(days=weekday)
        end_of_week = start_of_week + timedelta(days=6)
        start_str = start_of_week.isoformat()
        end_str = end_of_week.isoformat()
        week_number = target_date.isocalendar()[1]
        year = target_date.year

        briefings = self.db.get_briefings_by_range(start_str, end_str)
        quiz_scores = self.db.get_quiz_scores(start_str, end_str)
        learning_stats = self.db.get_learning_stats(start_str, end_str)
        all_content = self.db.get_content_by_date_range(start_str, end_str)

        briefing_summaries = ""
        for b in briefings:
            mod_label = self._module_label(b.get("module", "geo"))
            preview = (b["content"] or "")[:500]
            briefing_summaries += (
                f"\n### [{mod_label}] {b['date']}\n{preview}\n...\n"
            )

        scores_text = ""
        if quiz_scores:
            scores_list = [
                f"- {s['date']} [{self._module_label(s.get('module', 'geo'))}]: "
                f"{s['score']:.0f}分"
                for s in quiz_scores
            ]
            avg = sum(s["score"] for s in quiz_scores) / len(quiz_scores)
            scores_text = "\n".join(scores_list) + f"\n平均分: {avg:.1f}"
        else:
            scores_text = "本周暂无测验记录"

        stats_text = (
            f"- 学习天数: {learning_stats.get('active_days', 0)}\n"
            f"- 总学习时长: {learning_stats.get('total_minutes', 0)} 分钟\n"
            f"- 活动次数: {learning_stats.get('total_activities', 0)}\n"
            f"- 收集内容数: {len(all_content)}"
        )

        # 按模块统计内容数
        module_counts = {}
        for c in all_content:
            m = c.get("module", "geo")
            module_counts[m] = module_counts.get(m, 0) + 1
        module_stats = "\n".join(
            f"  - {self._module_label(m)}: {cnt} 篇"
            for m, cnt in module_counts.items()
        )

        start_date_str = self.settings.get("start_date", "2026-02-17")
        learning_start = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        days_learning = (target_date - learning_start).days + 1
        weeks_learning = days_learning // 7 + 1

        system_prompt = (
            "你是一位 AI 学习顾问和复盘教练。\n"
            "你需要生成一份涵盖多个学习模块（GEO、AI技术前沿、AI产品策略）的周度学习总结。\n"
            "使用中文输出，Markdown 格式。\n"
            "要有洞察力，能指出进步和需要改进的地方。"
        )

        user_prompt = f"""请生成第 {week_number} 周（{start_str} ~ {end_str}）的 AI 学习周报。
这是学习旅程的第 {weeks_learning} 周。

## 本周学习数据
{stats_text}

## 各模块内容统计
{module_stats if module_stats else "暂无数据"}

## 测验成绩
{scores_text}

## 本周简报内容摘要
{briefing_summaries if briefing_summaries else "本周暂无简报记录"}

---

请按以下结构生成周报：

# 📊 AI Learning Hub 周报 - 第 {week_number} 周
**{start_str} ~ {end_str}** | 学习旅程第 {weeks_learning} 周

## 📈 本周学习概览
（各模块的学习数据统计和总结）

## 🔑 本周核心收获
（跨模块总结本周最重要的3-5个学习收获）

## 📚 各模块亮点
### GEO 学习
### AI 技术前沿
### AI 产品 & 策略

## 💪 进步与亮点

## 🎯 待改进方向

## 🔮 下周学习建议

## 📝 一周感悟"""

        report = self.ai.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            use_advanced=True,
            max_tokens=4000,
        )

        self.db.save_weekly_report(
            week_number=week_number, year=year,
            start_date=start_str, end_date=end_str,
            content=report, module=module,
        )
        self._save_report_file(
            "weekly", f"week-{year}-W{week_number:02d}.md", report
        )
        return report

    def generate_monthly(self, target_date: date = None,
                         module: str = "all") -> str:
        if not target_date:
            target_date = date.today()

        month = target_date.month
        year = target_date.year
        start_of_month = target_date.replace(day=1)
        if month == 12:
            end_of_month = target_date.replace(
                year=year + 1, month=1, day=1
            ) - timedelta(days=1)
        else:
            end_of_month = target_date.replace(
                month=month + 1, day=1
            ) - timedelta(days=1)

        start_str = start_of_month.isoformat()
        end_str = end_of_month.isoformat()

        briefings = self.db.get_briefings_by_range(start_str, end_str)
        quiz_scores = self.db.get_quiz_scores(start_str, end_str)
        learning_stats = self.db.get_learning_stats(start_str, end_str)
        all_content = self.db.get_content_by_date_range(start_str, end_str)

        # 各模块月度主题
        month_themes = []
        start_date_str = self.settings.get("start_date", "2026-02-17")
        learning_start = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        months_elapsed = (
            (target_date.year - learning_start.year) * 12
            + (target_date.month - learning_start.month) + 1
        )
        months_elapsed = max(1, min(months_elapsed, 10))

        for mid, cfg in self.all_modules.items():
            track = cfg.get("learning_track", {})
            theme = track.get(f"month_{months_elapsed}", "综合学习")
            label = cfg.get("module_name", mid)
            month_themes.append(f"- {label}: {theme}")
        themes_text = "\n".join(month_themes)

        briefing_highlights = ""
        for b in briefings:
            mod_label = self._module_label(b.get("module", "geo"))
            briefing_highlights += (
                f"- [{mod_label}] {b['date']}: "
                f"{(b.get('content', '') or '')[:200]}...\n"
            )

        scores_text = ""
        if quiz_scores:
            avg = sum(s["score"] for s in quiz_scores) / len(quiz_scores)
            scores_text = (
                f"- 测验次数: {len(quiz_scores)}\n"
                f"- 平均分: {avg:.1f}\n"
                f"- 最高分: {max(s['score'] for s in quiz_scores):.1f}\n"
                f"- 最低分: {min(s['score'] for s in quiz_scores):.1f}"
            )
        else:
            scores_text = "本月暂无测验记录"

        stats_text = (
            f"- 活跃天数: {learning_stats.get('active_days', 0)}\n"
            f"- 总学习时长: {learning_stats.get('total_minutes', 0)} 分钟\n"
            f"- 收集内容数: {len(all_content)}\n"
            f"- 生成简报数: {len(briefings)}"
        )

        system_prompt = (
            "你是一位 AI 领域的资深导师和学习规划师。\n"
            "你需要生成一份涵盖多个学习模块的深度月度学习总结。\n"
            "使用中文输出，Markdown 格式。"
        )

        user_prompt = f"""请生成 {year}年{month}月 的 AI Learning Hub 月报。
这是学习旅程的第 {months_elapsed} 个月。

## 各模块本月主题
{themes_text}

## 本月学习数据
{stats_text}

## 测验成绩
{scores_text}

## 简报概览
{briefing_highlights if briefing_highlights else "本月暂无简报"}

---

请按以下结构生成月报：

# 📅 AI Learning Hub 月报 - {year}年{month}月
**学习旅程第 {months_elapsed} 个月**

## 📊 月度数据总览

## 🏆 本月核心成就

## 📚 各模块学习回顾
### GEO 学习
### AI 技术前沿
### AI 产品 & 策略

## 📈 行业趋势洞察

## 💡 深度洞察（跨模块）

## 🔍 学习效果评估

## 📋 知识清单

## 🎯 下月学习规划

## 💭 月度反思"""

        report = self.ai.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            use_advanced=True,
            max_tokens=5000,
        )

        combined_theme = " | ".join(
            f"{cfg.get('module_name', mid)}: "
            f"{cfg.get('learning_track', {}).get(f'month_{months_elapsed}', '')}"
            for mid, cfg in self.all_modules.items()
        )

        self.db.save_monthly_report(
            month=month, year=year, content=report,
            month_theme=combined_theme, module=module,
        )
        self._save_report_file(
            "monthly", f"monthly-{year}-{month:02d}.md", report
        )
        return report

    def _module_label(self, module_id: str) -> str:
        labels = {"geo": "GEO", "ai_tech": "AI技术", "ai_product": "AI产品"}
        return labels.get(module_id, module_id)

    def _save_report_file(self, report_type: str, filename: str,
                          content: str):
        report_dir = get_data_path(report_type)
        filepath = report_dir / filename
        filepath.write_text(content, encoding="utf-8")
        return filepath
