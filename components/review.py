"""学习复盘组件 — KPI + 热力图 + 周报/月报 + AI 行动洞察"""

from datetime import date, datetime, timedelta

import streamlit as st
import pandas as pd

from config.loader import load_settings
from tracker.progress import ProgressTracker
from styles.icons import icon, imd, iheader


def render_review(db):
    """渲染学习复盘页面"""
    settings = load_settings()
    today = date.today()
    today_str = today.isoformat()

    start_str = settings.get("start_date", "2026-02-17")
    start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
    days_elapsed = max((today - start_date).days + 1, 1)

    st.markdown(
        f'{iheader("bar-chart", "学习复盘", level=1, size=24)}',
        unsafe_allow_html=True,
    )
    st.caption(f"学习起始: {start_str}  |  已进行 {days_elapsed} 天")

    # ===== KPIs =====
    all_stats = db.get_learning_stats(start_date.isoformat(), today_str)
    all_scores = db.get_quiz_scores(start_date.isoformat(), today_str)
    tracker = ProgressTracker(db)
    streak = tracker.get_streak()

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        active = all_stats.get("active_days", 0) or 0
        k1.metric("连续学习", f"{streak['current_streak']} 天",
                  delta=f"活跃 {active} / {days_elapsed} 天")
    with k2:
        mins = all_stats.get("total_minutes", 0) or 0
        k2.metric("总学习时长", f"{mins // 60}h {mins % 60}m",
                  delta=f"日均 {mins // max(days_elapsed, 1)} 分钟")
    with k3:
        avg = sum(s["score"] for s in all_scores) / len(all_scores) if all_scores else 0
        k3.metric("测验均分", f"{avg:.0f} 分", delta=f"{len(all_scores)} 次测验")
    with k4:
        total_content = sum(
            len(db.get_content_by_module(m, limit=9999))
            for m in ["geo", "ai_papers", "creators"]
        )
        k4.metric("内容总量", f"{total_content} 条")

    st.divider()

    # ===== Charts =====
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown(
            f'{imd("calendar", "<b>最近 30 天学习热力图</b>", tag="h3", size=18)}',
            unsafe_allow_html=True,
        )
        recent_data = []
        for i in range(30):
            d = today - timedelta(days=29 - i)
            ds = d.isoformat()
            day_stats = db.get_learning_stats(ds, ds)
            recent_data.append({
                "日期": ds,
                "学习活动": (day_stats.get("total_activities", 0) or 0),
            })
        cal_df = pd.DataFrame(recent_data)
        cal_df["日期"] = pd.to_datetime(cal_df["日期"])
        cal_df = cal_df.set_index("日期")
        st.bar_chart(cal_df, use_container_width=True, height=220)

    with chart_col2:
        st.markdown(
            f'{imd("trending-up", "<b>测验成绩趋势</b>", tag="h3", size=18)}',
            unsafe_allow_html=True,
        )
        if all_scores:
            scores_df = pd.DataFrame(all_scores)
            scores_df["date"] = pd.to_datetime(scores_df["date"])
            scores_df["module_label"] = scores_df["module"].map(
                {"geo": "GEO", "ai_papers": "AI论文", "creators": "博主"}
            )
            chart_df = scores_df.pivot_table(
                index="date", columns="module_label", values="score", aggfunc="mean"
            )
            st.line_chart(chart_df, use_container_width=True, height=220)
        else:
            st.info("完成测验后显示成绩趋势。")

    st.divider()

    # ===== Tabs: Weekly / Monthly / Action Insights =====
    tab_weekly, tab_monthly, tab_actions = st.tabs([
        "周报", "月报", "AI 行动洞察"
    ])

    # --------- 周报 ---------
    with tab_weekly:
        weekday = today.weekday()
        start_of_week = today - timedelta(days=weekday)
        end_of_week = start_of_week + timedelta(days=6)
        week_number = today.isocalendar()[1]

        st.markdown(
            imd("trending-up", f"<b>第 {week_number} 周</b> ({start_of_week} ~ {end_of_week})", tag="h3", size=18),
            unsafe_allow_html=True,
        )

        w_stats = db.get_learning_stats(start_of_week.isoformat(), end_of_week.isoformat())
        w_scores = db.get_quiz_scores(start_of_week.isoformat(), end_of_week.isoformat())
        w_briefings = db.get_briefings_by_range(start_of_week.isoformat(), end_of_week.isoformat())

        wc1, wc2, wc3 = st.columns(3)
        wc1.metric("活跃天", f"{w_stats.get('active_days', 0) or 0}")
        wc2.metric("时长", f"{w_stats.get('total_minutes', 0) or 0} 分钟")
        w_avg = sum(s["score"] for s in w_scores) / len(w_scores) if w_scores else 0
        wc3.metric("均分", f"{w_avg:.0f}")

        sub_gen, sub_hist = st.tabs(["生成周报", "历史周报"])

        with sub_gen:
            weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            st.caption(f"今天{weekday_names[today.weekday()]}，建议周五生成周报。")
            if st.button("生成跨模块周报", type="primary",
                          use_container_width=True, key="rv_weekly"):
                if not settings["openai"]["api_key"]:
                    st.error("未设置 OPENAI_API_KEY")
                else:
                    from generators.summary_generator import SummaryGenerator
                    with st.spinner("AI 生成周度总结..."):
                        gen = SummaryGenerator(db)
                        report = gen.generate_weekly(today)
                        db.log_activity("weekly_review", 15,
                                        f"完成第{week_number}周总结")
                    st.success("周报生成完成！")
                    st.markdown(report)

        with sub_hist:
            cursor = db._execute("""
                SELECT * FROM weekly_reports
                ORDER BY year DESC, week_number DESC LIMIT 20
            """)
            reports = db._fetchall_as_dicts(cursor)
            if reports:
                for r in reports:
                    label = (f"{r['year']}年 第{r['week_number']}周 "
                             f"({r['start_date']} ~ {r['end_date']})")
                    with st.expander(label):
                        st.markdown(r["content"])
            else:
                st.info("暂无历史周报。")

    # --------- 月报 ---------
    with tab_monthly:
        st.markdown(
            imd("calendar", f"<b>{today.year}年{today.month}月</b>", tag="h3", size=18),
            unsafe_allow_html=True,
        )

        start_of_month = today.replace(day=1).isoformat()
        m_stats = db.get_learning_stats(start_of_month, today_str)
        m_scores = db.get_quiz_scores(start_of_month, today_str)
        m_briefings = db.get_briefings_by_range(start_of_month, today_str)
        m_content = db.get_content_by_date_range(start_of_month, today_str)

        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("活跃天", f"{m_stats.get('active_days', 0) or 0}")
        mc2.metric("时长", f"{m_stats.get('total_minutes', 0) or 0} 分钟")
        mc3.metric("简报", f"{len(m_briefings)}")
        mc4.metric("内容", f"{len(m_content)}")

        sub_gen_m, sub_hist_m = st.tabs(["生成月报", "历史月报"])

        with sub_gen_m:
            st.caption("建议在每月底或月初生成总结。")
            if st.button("生成跨模块月报", type="primary",
                          use_container_width=True, key="rv_monthly"):
                if not settings["openai"]["api_key"]:
                    st.error("未设置 OPENAI_API_KEY")
                else:
                    from generators.summary_generator import SummaryGenerator
                    with st.spinner("AI 生成月度总结..."):
                        gen = SummaryGenerator(db)
                        report = gen.generate_monthly(today)
                        db.log_activity("monthly_review", 30,
                                        f"完成{today.year}年{today.month}月总结")
                    st.success("月报生成完成！")
                    st.markdown(report)

        with sub_hist_m:
            cursor = db._execute("""
                SELECT * FROM monthly_reports
                ORDER BY year DESC, month DESC LIMIT 12
            """)
            reports = db._fetchall_as_dicts(cursor)
            if reports:
                for r in reports:
                    label = f"{r['year']}年{r['month']}月"
                    theme = r.get("month_theme", "")
                    if theme:
                        label += f" — {theme[:50]}"
                    with st.expander(label):
                        st.markdown(r["content"])
            else:
                st.info("暂无历史月报。")

    # --------- AI 行动洞察 ---------
    with tab_actions:
        st.markdown(
            f'{imd("lightbulb", "<b>高价值行动洞察</b>", tag="h3", size=18)}',
            unsafe_allow_html=True,
        )
        st.caption("AI 评分 >= 7 的内容，提炼的可落地启发和行动项")

        cursor = db._execute("""
            SELECT title, source, module, actionable_insight,
                   core_conclusion, ai_quality_score, tags, url
            FROM content_items
            WHERE ai_quality_score >= 7 AND actionable_insight != ''
            ORDER BY ai_quality_score DESC
            LIMIT 30
        """)
        high_value = db._fetchall_as_dicts(cursor)

        module_labels = {"geo": "GEO", "ai_papers": "论文", "creators": "博主"}
        module_pills = {
            "geo": '<span class="pill-geo">GEO</span>',
            "ai_papers": '<span class="pill-paper">论文</span>',
            "creators": '<span class="pill-creator">博主</span>',
        }

        if high_value:
            st.success(f"共 {len(high_value)} 条高价值内容")
            for i, item in enumerate(high_value, 1):
                mod = item.get("module", "")
                pill = module_pills.get(mod, "")
                qs = item.get("ai_quality_score", 0)

                st.markdown(
                    f"**{i}.** {pill} {item['title'][:60]}  "
                    f'<code style="font-size:0.7rem;">AI {qs:.0f}分</code>',
                    unsafe_allow_html=True,
                )
                if item.get("core_conclusion"):
                    st.markdown(f"  - 核心结论: {item['core_conclusion']}")
                if item.get("actionable_insight"):
                    st.markdown(f"  - **行动项: {item['actionable_insight']}**")
                if item.get("tags"):
                    st.markdown(
                        f'{icon("tag", 12)} <span style="font-size:0.7rem;color:#94A3B8;">{item["tags"]}</span>',
                        unsafe_allow_html=True,
                    )
                st.divider()
        else:
            st.info("暂无高评分内容。抓取并富化内容后，高价值行动洞察将显示在这里。")
