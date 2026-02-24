"""今日工作台组件 — 统一早报 + 快速抓取 + 每日测验"""

import json
from datetime import date, timedelta

import streamlit as st

from config.loader import load_settings
from styles.icons import icon, imd, iheader, DOT_GREEN, DOT_YELLOW, DOT_RED


MODULE_META = {
    "geo": {"icon": "globe", "label": "GEO"},
    "ai_tech": {"icon": "cpu", "label": "AI技术"},
    "ai_product": {"icon": "rocket", "label": "AI产品"},
}


def render_workbench(db):
    """渲染今日工作台页面"""
    settings = load_settings()
    today = date.today()
    today_str = today.isoformat()

    st.markdown(
        f'{iheader("rocket", "今日工作台", level=1, size=24)}',
        unsafe_allow_html=True,
    )
    st.caption(f"{today_str}")

    st.markdown(
        '<div style="background:rgba(96,165,250,0.08);border:1px solid rgba(96,165,250,0.15);'
        'border-radius:10px;padding:0.6rem 1rem;margin:0.5rem 0 1rem;font-size:0.8rem;color:#94A3B8;">'
        f'{icon("lightbulb", 14)} '
        '<b style="color:#F1F5F9;">30 分钟流程:</b> '
        '阅读早报 (15m) → 深读原文 (10m) → 做测验巩固 (5m)'
        '</div>',
        unsafe_allow_html=True,
    )

    unified = db.get_briefing(today_str, module="unified")

    st.divider()

    # =============================================
    # SECTION 1: 统一早报
    # =============================================
    if unified:
        st.markdown(
            f'{iheader("sun", "今日统一早报", level=2, size=20)}',
            unsafe_allow_html=True,
        )

        tab_unified, tab_geo, tab_tech, tab_product, tab_history = st.tabs([
            "统一早报", "GEO", "AI技术", "AI产品", "历史"
        ])

        with tab_unified:
            st.markdown(unified["content"])
            db.log_activity("briefing_read", 15, f"阅读 {today_str} 统一早报", "geo")

        for tab, mid in [(tab_geo, "geo"), (tab_tech, "ai_tech"), (tab_product, "ai_product")]:
            with tab:
                mod_b = db.get_briefing(today_str, module=mid)
                if mod_b:
                    st.markdown(mod_b["content"])
                else:
                    st.info(f"{MODULE_META[mid]['label']} 单模块早报尚未生成")

        with tab_history:
            week_ago = (today - timedelta(days=7)).isoformat()
            history = db.get_briefings_by_range(week_ago, today_str, "unified")
            if history:
                sel = st.selectbox("选择日期",
                                   [b["date"] for b in reversed(history)],
                                   key="wb_hist")
                for b in history:
                    if b["date"] == sel:
                        st.markdown(b["content"])
                        break
            else:
                st.info("暂无历史早报")

        _render_grok_import(db)

    else:
        st.markdown(
            f'{iheader("sun", "生成今日早报", level=2, size=20)}',
            unsafe_allow_html=True,
        )
        st.info("今日统一早报尚未生成。先抓取内容，再一键生成。")

        st.markdown(
            f'<p style="color:#94A3B8;font-size:0.85rem;margin:0.5rem 0 0.25rem;">'
            f'{icon("download", 14)} <b>快速抓取内容</b></p>',
            unsafe_allow_html=True
        )
        with st.container():
            sc1, sc2, sc3 = st.columns(3)

            with sc1:
                if st.button("抓取 GEO", use_container_width=True, key="wb_geo"):
                    with st.spinner("抓取 GEO 高频源..."):
                        from scrapers.rss_scraper import RSSScraper
                        from processors.content_processor import ContentProcessor
                        scraper = RSSScraper(module="geo")
                        items = scraper.fetch_all(verbose=False, frequency="daily")
                        proc = ContentProcessor(db, module="geo")
                        stats = proc.process_and_save(items)
                        st.success(f"GEO: 新增 {stats['new_saved']} / 总 {stats['total_fetched']}")

            with sc2:
                if st.button("抓取 AI技术", use_container_width=True, key="wb_tech"):
                    with st.spinner("抓取 AI 技术前沿..."):
                        from scrapers.rss_scraper import RSSScraper
                        from processors.content_processor import ContentProcessor
                        items = []
                        try:
                            from scrapers.arxiv_scraper import ArxivScraper
                            items = ArxivScraper(module="ai_tech").fetch_all(verbose=False)
                        except ImportError:
                            pass
                        try:
                            from scrapers.youtube_scraper import YouTubeScraper
                            items.extend(YouTubeScraper(module="ai_tech").fetch_all(verbose=False))
                        except Exception:
                            pass
                        rss = RSSScraper(module="ai_tech")
                        items.extend(rss.fetch_all(verbose=False))
                        proc = ContentProcessor(db, module="ai_tech")
                        stats = proc.process_and_save(items)
                        st.success(f"AI技术: 新增 {stats['new_saved']} / 总 {stats['total_fetched']}")

            with sc3:
                if st.button("抓取 AI产品", use_container_width=True, key="wb_product"):
                    with st.spinner("抓取 AI 产品 & 策略..."):
                        from scrapers.rss_scraper import RSSScraper
                        from processors.content_processor import ContentProcessor
                        items = []
                        try:
                            from scrapers.youtube_scraper import YouTubeScraper
                            items.extend(YouTubeScraper().fetch_all(verbose=False))
                        except Exception:
                            pass
                        rss = RSSScraper(module="ai_product")
                        items.extend(rss.fetch_all(verbose=False))
                        proc = ContentProcessor(db, module="ai_product")
                        stats = proc.process_and_save(items)
                        st.success(f"AI产品: 新增 {stats['new_saved']} / 总 {stats['total_fetched']}")

            for mid, meta in MODULE_META.items():
                unused = len(db.get_unused_content(mid, limit=999))
                st.caption(f"{meta['label']}：{unused} 条待使用")

        _render_grok_import(db)

        if st.button("生成今日统一早报", type="primary",
                      use_container_width=True, key="wb_gen_unified"):
            if not settings["openai"]["api_key"]:
                st.error("未设置 OPENAI_API_KEY")
            else:
                from generators.daily_briefing import DailyBriefingGenerator
                from processors.content_processor import ContentProcessor

                with st.spinner("AI 富化内容中..."):
                    proc = ContentProcessor(db)
                    unenriched = db.get_unenriched_content(limit=20)
                    if unenriched:
                        proc.enrich_with_ai(unenriched)

                with st.spinner("生成统一早报中..."):
                    gen = DailyBriefingGenerator(db, module="geo")
                    content = gen.generate_unified(today_str)
                    db.log_activity("briefing_generated", 5,
                                    f"生成 {today_str} 统一早报", "geo")

                st.success("早报生成完成！")
                st.rerun()

    st.divider()

    # =============================================
    # SECTION 2: 每日测验（统一 10 道选择题）
    # =============================================
    st.markdown(
        f'{iheader("pencil", "每日测验", level=2, size=20)}',
        unsafe_allow_html=True,
    )

    from generators.quiz_generator import QuizGenerator
    quiz_gen = QuizGenerator(db, module="unified")

    qd_key = "wb_qd_unified"
    qs_key = "wb_qs_unified"
    qe_key = "wb_qe_unified"

    if qd_key not in st.session_state:
        st.session_state[qd_key] = None
    if qs_key not in st.session_state:
        st.session_state[qs_key] = False
    if qe_key not in st.session_state:
        st.session_state[qe_key] = None

    briefing = db.get_briefing(today_str, module="unified")

    if not briefing:
        st.caption("需要先生成统一早报才能进行测验。")
    else:
        existing_quiz = db.get_quiz(today_str, module="unified")

        if existing_quiz and existing_quiz.get("completed") and not st.session_state[qs_key]:
            quiz_data = json.loads(existing_quiz["questions"])
            evaluation = json.loads(existing_quiz["answers"]) if existing_quiz.get("answers") else None
            if evaluation:
                rc1, rc2 = st.columns(2)
                rc1.metric("得分", f"{evaluation['percentage']:.1f}%",
                           delta=f"{evaluation['total_score']}/{evaluation['max_score']}")
                rc2.metric("状态", "通过" if evaluation["passed"] else "未通过")
            with st.expander("答案解析", expanded=False):
                st.markdown(quiz_gen.format_answers_for_display(quiz_data))
            if st.button("重新测验", key="wb_retake"):
                st.session_state[qd_key] = None
                st.session_state[qs_key] = False
                st.session_state[qe_key] = None
                if "wb_ans_unified" in st.session_state:
                    del st.session_state["wb_ans_unified"]
                st.rerun()

        elif st.session_state[qd_key] is None:
            if existing_quiz and not existing_quiz.get("completed"):
                st.session_state[qd_key] = json.loads(existing_quiz["questions"])
                st.rerun()
            else:
                st.caption("共 10 道选择题 | 每题 10 分 | 满分 100 分 | 及格 60 分")
                if st.button("开始测验", type="primary",
                              use_container_width=True, key="wb_start_quiz"):
                    if not settings["openai"]["api_key"]:
                        st.error("未设置 OPENAI_API_KEY")
                    else:
                        with st.spinner("生成测验题目..."):
                            quiz_data = quiz_gen.generate_quiz(briefing["content"], today_str)
                        if "error" in quiz_data:
                            st.error(f"生成失败: {quiz_data['error']}")
                        else:
                            st.session_state[qd_key] = quiz_data
                            st.rerun()

        if st.session_state[qd_key] is not None:
            quiz_data = st.session_state[qd_key]
            questions = quiz_data.get("questions", [])
            title = quiz_data.get("quiz_title", "每日测验")

            if not st.session_state[qs_key]:
                st.markdown(
                    imd("clipboard", f"<b>{title}</b>"),
                    unsafe_allow_html=True,
                )
                st.caption(f"共 {len(questions)} 题 | 每题 10 分 | 及格 60 分")

                with st.form("wb_quiz_form"):
                    user_answers = {}
                    for q in questions:
                        q_id = str(q.get("id", ""))
                        diff = q.get("difficulty", "medium")
                        diff_map = {
                            "easy": f"{DOT_GREEN()} 简单",
                            "medium": f"{DOT_YELLOW()} 中等",
                            "hard": f"{DOT_RED()} 困难",
                        }

                        st.markdown(
                            f"**第 {q_id} 题** {diff_map.get(diff, '')}",
                            unsafe_allow_html=True,
                        )
                        st.markdown(f"{q['question']}")

                        ans = st.radio("选择", q.get("options", []),
                                       key=f"wb_q_unified_{q_id}",
                                       index=None, label_visibility="collapsed")
                        if ans:
                            user_answers[q_id] = ans[0]
                        st.divider()

                    if st.form_submit_button("提交答案", type="primary",
                                              use_container_width=True):
                        unanswered = [str(q["id"]) for q in questions
                                      if str(q["id"]) not in user_answers]
                        if unanswered:
                            st.warning(f"第 {', '.join(unanswered)} 题未作答")
                        else:
                            st.session_state["wb_ans_unified"] = user_answers
                            st.session_state[qs_key] = True
                            st.rerun()

            if st.session_state[qs_key] and st.session_state[qe_key] is None:
                with st.spinner("评估中..."):
                    evaluation = quiz_gen.evaluate_answers(
                        quiz_data, st.session_state["wb_ans_unified"])
                    st.session_state[qe_key] = evaluation
                    db.log_activity("quiz_completed", 10,
                                    f"测验: {evaluation['percentage']:.1f}%",
                                    "unified")
                st.rerun()

            if st.session_state[qe_key]:
                evaluation = st.session_state[qe_key]
                if evaluation["passed"]:
                    st.success(f"恭喜通过！{evaluation['summary']}")
                    st.balloons()
                else:
                    st.error(f"继续加油！{evaluation['summary']}")

                ec1, ec2, ec3 = st.columns(3)
                ec1.metric("得分", f"{evaluation['total_score']}/{evaluation['max_score']}")
                ec2.metric("百分比", f"{evaluation['percentage']:.1f}%")
                ec3.metric("状态", "通过" if evaluation["passed"] else "未通过")

                with st.expander("详细解析", expanded=True):
                    for r in evaluation.get("results", []):
                        i_icon = icon("check", 14, color="#4ADE80") if r.get("correct") else icon("x-circle", 14, color="#F87171")
                        st.markdown(
                            f"{i_icon} **第 {r['question_id']} 题** "
                            f"({r['score']}/{r['max_score']})",
                            unsafe_allow_html=True,
                        )
                        st.markdown(f"**反馈：** {r['feedback']}")
                        st.divider()

                if st.button("重新测验", key="wb_retake2"):
                    st.session_state[qd_key] = None
                    st.session_state[qs_key] = False
                    st.session_state[qe_key] = None
                    if "wb_ans_unified" in st.session_state:
                        del st.session_state["wb_ans_unified"]
                    st.rerun()


def _render_grok_import(db):
    """渲染 Grok 简报导入区域"""
    from scrapers.grok_importer import parse_grok_markdown
    from processors.content_processor import ContentProcessor

    with st.expander("📋 导入 Grok 简报", expanded=False):
        st.caption("粘贴 Grok 生成的 Markdown 简报，一键导入到知识库")

        grok_text = st.text_area(
            "Grok 简报内容",
            height=250,
            placeholder="在这里粘贴 Grok 输出的 Markdown 简报...\n\n"
                        "例如:\n"
                        "AI 情报简报 | 2026-02-24\n"
                        "📌 今日一句话：...\n"
                        "🔍 AI 搜索 & GEO\n"
                        "...",
            key="wb_grok_input",
            label_visibility="collapsed",
        )

        if st.button("导入", type="primary", use_container_width=True,
                      key="wb_grok_import"):
            if not grok_text or len(grok_text.strip()) < 50:
                st.warning("内容太短，请粘贴完整的 Grok 简报")
            else:
                with st.spinner("解析并导入中..."):
                    result = parse_grok_markdown(grok_text)
                    items = result["items"]

                    if not items:
                        st.warning("未能解析出任何条目，请检查格式")
                    else:
                        total_new = 0
                        module_stats = {}
                        for module_id in ["geo", "ai_tech", "ai_product"]:
                            mod_items = [it for it in items if it["module"] == module_id]
                            if not mod_items:
                                continue
                            proc = ContentProcessor(db, module=module_id)
                            stats = proc.process_and_save(mod_items)
                            total_new += stats["new_saved"]
                            module_stats[module_id] = stats["new_saved"]

                        counts = result["section_counts"]
                        detail = " · ".join(
                            f"{MODULE_META.get(m, {}).get('label', m)} {c}条"
                            for m, c in counts.items()
                        )

                        if result["highlight"]:
                            st.info(f"📌 {result['highlight']}")

                        st.success(
                            f"导入完成！解析 {len(items)} 条（{detail}），"
                            f"新增 {total_new} 条入库"
                        )

                        db.log_activity(
                            "grok_import", 5,
                            f"导入 Grok 简报: {len(items)} 条, 新增 {total_new}",
                            "geo",
                        )
