"""学习进度追踪 - 多模块可视化学习历程"""

from datetime import date, datetime, timedelta

from config.loader import load_settings, load_all_module_configs
from tracker.database import Database


class ProgressTracker:
    """多模块学习进度追踪器"""

    def __init__(self, db: Database = None):
        self.db = db or Database()
        self.settings = load_settings()
        self.all_modules = load_all_module_configs()

    def get_overview(self, module: str = None) -> str:
        start_str = self.settings.get("start_date", "2026-02-17")
        start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
        today = date.today()

        days_elapsed = (today - start_date).days + 1
        total_days = 300
        progress_pct = min(days_elapsed / total_days * 100, 100)

        months_elapsed = (
            (today.year - start_date.year) * 12
            + (today.month - start_date.month) + 1
        )
        months_elapsed = max(1, min(months_elapsed, 10))

        all_stats = self.db.get_learning_stats(
            start_date.isoformat(), today.isoformat(), module
        )
        all_scores = self.db.get_quiz_scores(
            start_date.isoformat(), today.isoformat(), module
        )

        bar_length = 30
        filled = int(bar_length * progress_pct / 100)
        bar = "█" * filled + "░" * (bar_length - filled)

        lines = [
            "# 🎓 AI Learning Hub 学习进度总览",
            "",
            f"**学习起始日**: {start_str}",
            f"**已学习天数**: {days_elapsed} 天",
            "",
            f"## 📊 总进度: {progress_pct:.1f}%",
            f"`[{bar}]` {days_elapsed}/{total_days} 天",
            "",
            "## 📈 累计数据",
            f"- 🗓 活跃天数: {all_stats.get('active_days', 0)}",
            f"- ⏱ 总学习时长: {all_stats.get('total_minutes', 0)} 分钟",
            f"- 📝 完成测验: {len(all_scores)} 次",
        ]

        if all_scores:
            avg = sum(s["score"] for s in all_scores) / len(all_scores)
            lines.append(f"- 📊 平均测验分数: {avg:.1f}")

        lines.extend(["", "## 🗺 各模块学习路径"])

        for mid, cfg in self.all_modules.items():
            label = cfg.get("module_name", mid)
            track = cfg.get("learning_track", {})
            lines.append(f"\n### {label}")
            for i in range(1, 11):
                theme = track.get(f"month_{i}", "待定")
                if i < months_elapsed:
                    status = "✅"
                elif i == months_elapsed:
                    status = "🔄"
                else:
                    status = "⬜"
                lines.append(f"  {status} 第{i}月: {theme}")

        return "\n".join(lines)

    def get_streak(self) -> dict:
        today = date.today()
        start_str = self.settings.get("start_date", "2026-02-17")

        stats = self.db.get_learning_stats(start_str, today.isoformat())
        active_days = stats.get("active_days", 0)

        current_streak = 0
        check_date = today
        while True:
            day_stats = self.db.get_learning_stats(
                check_date.isoformat(), check_date.isoformat()
            )
            if day_stats.get("total_activities", 0) and \
               day_stats["total_activities"] > 0:
                current_streak += 1
                check_date -= timedelta(days=1)
            else:
                break

        return {
            "current_streak": current_streak,
            "total_active_days": active_days or 0,
        }
