"""知识库组件 — 跨模块搜索、浏览、手动录入"""

from datetime import date, datetime

import streamlit as st
import pandas as pd

from styles.icons import icon, imd, iheader


MODULE_LABELS = {
    "geo": "GEO",
    "ai_papers": "AI论文",
    "creators": "博主",
}

MODULE_PILL = {
    "geo": '<span class="pill-geo">GEO</span>',
    "ai_papers": '<span class="pill-paper">论文</span>',
    "creators": '<span class="pill-creator">博主</span>',
}

TYPE_ICONS = {
    "article": "file-text",
    "paper": "file-text",
    "video": "video",
    "podcast": "satellite",
    "note": "bird",
}

ARXIV_TAGS_CN = {
    "cs.AI": "人工智能",
    "cs.CL": "NLP",
    "cs.LG": "机器学习",
    "cs.CV": "计算机视觉",
    "cs.RO": "机器人",
    "cs.NE": "神经进化",
    "cs.IR": "信息检索",
    "cs.HC": "人机交互",
    "cs.SE": "软件工程",
    "cs.PL": "编程语言",
    "cs.DC": "分布式计算",
    "cs.CR": "密码安全",
    "stat.ML": "统计ML",
    "eess.SY": "系统控制",
    "eess.AS": "音频语音",
    "eess.IV": "图像视频",
    "math.OC": "优化控制",
    "q-bio.NC": "神经计算",
}


def translate_tags(tags_str: str) -> str:
    """将 arXiv 分类标签转为中文"""
    if not tags_str:
        return ""
    parts = [t.strip() for t in tags_str.split(",")]
    translated = [ARXIV_TAGS_CN.get(p, p) for p in parts]
    return ", ".join(translated)


def render_knowledge(db):
    """渲染知识库页面"""
    today_str = date.today().isoformat()

    st.markdown(
        f'{iheader("books", "知识库", level=1, size=24)}',
        unsafe_allow_html=True,
    )
    st.caption("搜索、浏览你积累的所有学习内容")

    # ===== Search Bar =====
    search_q = st.text_input(
        "搜索", placeholder="输入关键词搜索标题、摘要和标签...",
        key="kb_search", label_visibility="collapsed",
    )

    # ===== Filter Row =====
    fc1, fc2, fc3 = st.columns([1, 1, 1])

    with fc1:
        module_filter = st.selectbox(
            "模块",
            ["全部", "geo", "ai_papers", "creators"],
            format_func=lambda x: "全部模块" if x == "全部" else MODULE_LABELS.get(x, x),
            key="kb_module_filter",
        )
    with fc2:
        type_filter = st.selectbox(
            "类型",
            ["全部", "article", "paper", "video", "podcast", "note"],
            key="kb_type_filter",
        )
    with fc3:
        sort_options = {
            "最新优先": "fetched_at DESC",
            "AI 评分最高": "ai_quality_score DESC",
            "相关度最高": "relevance_score DESC",
        }
        sort_by = st.selectbox("排序", list(sort_options.keys()), key="kb_sort")

    st.divider()

    # ===== Tabs =====
    tab_content, tab_kb, tab_stats, tab_manual = st.tabs([
        "内容库", "知识条目", "信息源统计", "手动录入"
    ])

    # --------- 内容库 ---------
    with tab_content:
        query = "SELECT * FROM content_items WHERE 1=1"
        params = []

        if search_q:
            query += " AND (title LIKE ? OR summary LIKE ? OR tags LIKE ?)"
            params.extend([f"%{search_q}%", f"%{search_q}%", f"%{search_q}%"])
        if module_filter != "全部":
            query += " AND module = ?"
            params.append(module_filter)
        if type_filter != "全部":
            query += " AND content_type = ?"
            params.append(type_filter)

        query += f" ORDER BY {sort_options[sort_by]} LIMIT 50"
        cursor = db.conn.execute(query, params)
        items = [dict(row) for row in cursor.fetchall()]

        st.caption(f"共 {len(items)} 条" + (" (显示前50条)" if len(items) == 50 else ""))

        if items:
            for item in items:
                score = item.get("relevance_score", 0)
                qs = item.get("ai_quality_score", 0)
                mod = item.get("module", "")
                mod_pill = MODULE_PILL.get(mod, "")
                type_ico_name = TYPE_ICONS.get(item.get("content_type", ""), "file-text")

                qi_badge = ""
                if qs >= 7:
                    qi_badge = icon("flame", 14, color="#F87171")
                elif qs >= 4:
                    qi_badge = icon("star", 14, color="#FACC15")

                type_ico = icon(type_ico_name, 14)
                title = item.get("title", "")[:80]
                source = item.get("source", "")
                conclusion = item.get("core_conclusion", "")
                tags = item.get("tags", "")
                url = item.get("url", "")
                published = (item.get("published_at", "") or "")[:10]
                status = "已学习" if item.get("used_in_briefing") else "待学习"

                tags_cn = translate_tags(tags)
                tags_line = f'<div class="content-card-tags">{tags_cn}</div>' if tags_cn else ""

                st.markdown(f"""
<div class="content-card">
    <div class="content-card-header">
        {qi_badge} {type_ico} {mod_pill}
        <span class="content-card-title">{title}</span>
    </div>
    <div class="content-card-meta">
        {source} · AI {qs:.0f}分 · {published} · {status}
    </div>
    {tags_line}
</div>
""", unsafe_allow_html=True)
                if url and not url.startswith("manual://"):
                    st.link_button("查看原文", url, use_container_width=False)

        else:
            st.info("暂无内容。去「今日工作台」抓取内容后，将显示在这里。")

    # --------- 知识条目 ---------
    with tab_kb:
        st.markdown(
            f'{imd("brain", "<b>知识条目</b>", tag="h3", size=18)}',
            unsafe_allow_html=True,
        )

        col_ks, col_km = st.columns([3, 1])
        with col_ks:
            kb_kw = st.text_input("搜索知识库",
                                   placeholder="输入关键词...",
                                   key="kb_kw_search")
        with col_km:
            kb_mod = st.selectbox(
                "模块", ["全部", "geo", "ai_papers", "creators"],
                format_func=lambda x: "全部" if x == "全部" else MODULE_LABELS.get(x, x),
                key="kb_kw_mod",
            )

        mod_param = None if kb_mod == "全部" else kb_mod

        if kb_kw:
            results = db.search_knowledge(kb_kw, mod_param)
            if results:
                for item in results:
                    mod_label = MODULE_LABELS.get(item.get("module", ""), "")
                    topic = item.get("topic", "")
                    category = item.get("category", "")
                    content = item.get("content", "")
                    tags = item.get("tags", "")
                    cross = item.get("cross_modules", "")
                    updated = (item.get("updated_at", "") or "")[:10]

                    content_preview = content[:300] + ("..." if len(content) > 300 else "")
                    tags_cn = translate_tags(tags)
                    tags_line = f'<div class="content-card-tags">{tags_cn}</div>' if tags_cn else ""
                    cross_line = f'<div class="content-card-tags">跨模块: {cross}</div>' if cross else ""

                    st.markdown(f"""
<div class="content-card">
    <div class="content-card-header">
        <span class="content-card-title">{mod_label} — {topic} [{category}]</span>
    </div>
    <div class="content-card-conclusion">{content_preview}</div>
    <div class="content-card-meta">更新: {updated}</div>
    {tags_line}
    {cross_line}
</div>
""", unsafe_allow_html=True)
            else:
                st.info(f"未找到与「{kb_kw}」相关的知识条目。")
        else:
            q = "SELECT * FROM knowledge_base"
            p = []
            if mod_param:
                q += " WHERE module = ?"
                p.append(mod_param)
            q += " ORDER BY updated_at DESC LIMIT 20"

            cursor = db.conn.execute(q, p)
            kb_items = [dict(row) for row in cursor.fetchall()]

            if kb_items:
                for item in kb_items:
                    mod_label = MODULE_LABELS.get(item.get("module", ""), "")
                    topic = item.get("topic", "")
                    category = item.get("category", "")
                    content = item.get("content", "")
                    tags = item.get("tags", "")

                    content_preview = content[:300] + ("..." if len(content) > 300 else "")
                    tags_cn = translate_tags(tags)
                    tags_line = f'<div class="content-card-tags">{tags_cn}</div>' if tags_cn else ""

                    st.markdown(f"""
<div class="content-card">
    <div class="content-card-header">
        <span class="content-card-title">{mod_label} — {topic} [{category}]</span>
    </div>
    <div class="content-card-conclusion">{content_preview}</div>
    {tags_line}
</div>
""", unsafe_allow_html=True)
            else:
                st.info("知识库暂时为空。随着学习积累，知识条目将在这里显示。")

    # --------- 信息源统计 ---------
    with tab_stats:
        st.markdown(
            f'{imd("bar-chart", "<b>信息源统计</b>", tag="h3", size=18)}',
            unsafe_allow_html=True,
        )

        cursor = db.conn.execute("""
            SELECT module, source, platform,
                   COUNT(*) as item_count,
                   AVG(relevance_score) as avg_relevance,
                   AVG(ai_quality_score) as avg_quality,
                   MAX(fetched_at) as last_fetched
            FROM content_items
            GROUP BY module, source
            ORDER BY item_count DESC
        """)
        source_stats = [dict(row) for row in cursor.fetchall()]

        if source_stats:
            stats_df = pd.DataFrame(source_stats)
            stats_df["module_label"] = stats_df["module"].map(
                {"geo": "GEO", "ai_papers": "AI论文", "creators": "博主"}
            )
            stats_df["avg_relevance"] = stats_df["avg_relevance"].round(2)
            stats_df["avg_quality"] = stats_df["avg_quality"].round(1)

            module_counts = stats_df.groupby("module_label")["item_count"].sum()
            st.markdown("#### 各模块内容占比")
            st.bar_chart(module_counts, use_container_width=True)

            st.markdown("#### 详细数据")
            display = stats_df[["module_label", "source", "platform",
                                 "item_count", "avg_relevance", "avg_quality"]].copy()
            display.columns = ["模块", "信息源", "平台", "内容数", "平均相关度", "平均AI评分"]
            st.dataframe(display, use_container_width=True, hide_index=True)

            total = sum(s["item_count"] for s in source_stats)
            st.caption(f"共 {len(source_stats)} 个信息源，{total} 条内容")
        else:
            st.info("暂无统计数据。抓取内容后将显示统计。")

    # --------- 手动录入 ---------
    with tab_manual:
        st.markdown(
            f'{imd("pencil", "<b>手动录入内容</b>", tag="h3", size=18)}',
            unsafe_allow_html=True,
        )
        st.caption("看到好内容？手动记录下来，纳入知识库。")

        with st.form("kb_manual_form", clear_on_submit=True):
            col_t, col_s = st.columns([2, 1])
            with col_t:
                title = st.text_input("标题 *", placeholder="视频/文章标题")
            with col_s:
                creator = st.text_input("博主/作者", placeholder="作者名")

            url = st.text_input("链接", placeholder="https://... (可选)")

            col_p, col_tp = st.columns(2)
            with col_p:
                platform = st.selectbox("平台",
                                         ["youtube", "twitter", "podcast", "wechat", "other"])
            with col_tp:
                content_type = st.selectbox("类型",
                                             ["video", "article", "note", "podcast"])

            notes = st.text_area("笔记 / 核心要点",
                                  placeholder="记录最有价值的内容...", height=150)
            tags = st.text_input("标签", placeholder="用逗号分隔，如: AI产品,增长,工具")

            submitted = st.form_submit_button("保存", type="primary",
                                               use_container_width=True)
            if submitted:
                if not title:
                    st.warning("请填写标题")
                else:
                    if not url:
                        url = f"manual://{platform}/{creator}/{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    item = {
                        "module": "creators",
                        "content_type": content_type,
                        "title": title,
                        "url": url,
                        "source": creator or "手动录入",
                        "platform": platform,
                        "category": "manual",
                        "summary": notes[:500] if notes else "",
                        "content": notes or "",
                        "creator_name": creator or "",
                        "tags": tags,
                        "relevance_score": 0.5,
                    }
                    saved = db.save_content_item(item)
                    if saved:
                        db.log_activity("manual_input", 5, f"手动录入: {title}", "creators")
                        st.success(f"已保存: {title}")
                    else:
                        st.warning("内容可能已存在（链接重复）")
