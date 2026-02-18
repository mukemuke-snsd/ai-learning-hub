"""Shared sidebar component for all pages."""

import streamlit as st
from datetime import date

from styles.icons import icon


MODULE_META = {
    "geo": {"icon": "globe", "label": "GEO"},
    "ai_papers": {"icon": "file-text", "label": "论文"},
    "creators": {"icon": "video", "label": "博主"},
}


def render_sidebar(db):
    """Render the unified sidebar across all pages.
    
    Args:
        db: Database instance for checking today's status
        
    Returns:
        tuple: (unified_briefing, quiz_done)
    """
    today_str = date.today().isoformat()
    
    unified = db.get_briefing(today_str, module="unified")
    quiz_done = any(
        (db.get_quiz(today_str, module=m) or {}).get("completed")
        for m in MODULE_META
    )
    
    with st.sidebar:
        # Brand
        st.markdown(
            f'<div class="sidebar-brand">{icon("brain", 22)} <span>AI Learning Hub</span></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p class="sidebar-tagline">每天 30 分钟，构建 AI 知识体系</p>',
            unsafe_allow_html=True,
        )

        st.markdown('<div class="sidebar-spacer"></div>', unsafe_allow_html=True)

        # Today's checklist
        st.markdown('<p class="sidebar-section-label">今日进度</p>', unsafe_allow_html=True)

        chk_b = icon("check-square", 15, color="#4ADE80") if unified else icon("square", 15, color="#475569")
        chk_q = icon("check-square", 15, color="#4ADE80") if quiz_done else icon("square", 15, color="#475569")
        briefing_cls = "done" if unified else "pending"
        quiz_cls = "done" if quiz_done else "pending"

        st.markdown(f"""
<div class="sidebar-checklist">
    <div class="checklist-item {briefing_cls}">{chk_b} <span>阅读早报</span></div>
    <div class="checklist-item {quiz_cls}">{chk_q} <span>完成测验</span></div>
</div>
""", unsafe_allow_html=True)

        st.markdown('<div class="sidebar-spacer"></div>', unsafe_allow_html=True)

        # Method tip
        st.markdown(
            '<div class="sidebar-tip">'
            f'{icon("lightbulb", 13)} <b>30 分钟流程</b><br>'
            '<span>早报 15m → 原文 10m → 测验 5m</span>'
            '</div>',
            unsafe_allow_html=True,
        )
    
    return unified, quiz_done
