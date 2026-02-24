"""
AI Learning Hub - 统一学习平台
==============================
启动方式: streamlit run app.py
"""

import sys
from pathlib import Path
from datetime import date

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

from config.loader import load_settings
from tracker.database import Database
from tracker.progress import ProgressTracker

st.set_page_config(
    page_title="AI Learning Hub",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

from styles.ocean_theme import get_ocean_css
from styles.icons import icon, imd
from components.sidebar import render_sidebar
from components.workbench import render_workbench
from components.knowledge import render_knowledge
from components.review import render_review

st.markdown(get_ocean_css(), unsafe_allow_html=True)


@st.cache_resource
def get_database():
    return Database(check_same_thread=False)


db = get_database()
settings = load_settings()
today = date.today()
today_str = today.isoformat()

MODULE_META = {
    "geo": {"icon": "globe", "label": "GEO"},
    "ai_tech": {"icon": "cpu", "label": "AI技术"},
    "ai_product": {"icon": "rocket", "label": "AI产品"},
}

# =============================================
# NAVIGATION STATE
# =============================================
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"

# Render shared sidebar and get navigation
unified, quiz_done = render_sidebar(db)


# =============================================
# SIDEBAR NAVIGATION (Compact Icon Style)
# =============================================
with st.sidebar:
    st.markdown('<div class="sidebar-section-label">导航</div>', unsafe_allow_html=True)

    nav_items = [
        ("home", "首页", "🏠"),
        ("workbench", "工作台", "🚀"),
        ("knowledge", "知识库", "📚"),
        ("review", "复盘", "📊"),
    ]

    nav_cols = st.columns(4)
    for i, (page_id, label, emoji_icon) in enumerate(nav_items):
        with nav_cols[i]:
            is_active = st.session_state.current_page == page_id
            btn_cls = "icon-nav-btn active" if is_active else "icon-nav-btn"
            if st.button(emoji_icon, key=f"nav_{page_id}", use_container_width=True,
                        help=label):
                st.session_state.current_page = page_id
                st.rerun()


# =============================================
# PAGE ROUTER
# =============================================
def render_home():
    """渲染首页"""
    st.markdown(
        f'<p class="main-header">{icon("brain", 28)} AI Learning Hub</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p class="sub-header">{icon("sun", 16)} {today_str} — 每天 30 分钟，构建你的 AI 知识体系</p>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'{imd("sparkles", "开始今天的学习", tag="h3", size=20)}',
        unsafe_allow_html=True,
    )

    nc1, nc2, nc3 = st.columns(3)

    total_content = sum(len(db.get_content_by_module(m, limit=9999)) for m in MODULE_META)
    tracker = ProgressTracker(db)
    streak = tracker.get_streak()

    with nc1:
        st.markdown(f"""
<div class="nav-card">
    <div class="card-icon">{icon("rocket", 32)}</div>
    <div class="card-title">今日工作台</div>
    <div class="card-desc">阅读早报 · 做测验 · 快速抓取</div>
</div>
""", unsafe_allow_html=True)
        status_txt = "早报已就绪" if unified else "等待生成"
        status_ico = icon("check", 14, color="#4ADE80") if unified else icon("clock", 14, color="#64748B")
        st.markdown(
            f'<span style="font-size:0.75rem;color:#94A3B8;">{status_ico} {status_txt}</span>',
            unsafe_allow_html=True,
        )
        if st.button("进入工作台", key="home_to_wb", use_container_width=True):
            st.session_state.current_page = "workbench"
            st.rerun()

    with nc2:
        st.markdown(f"""
<div class="nav-card">
    <div class="card-icon">{icon("books", 32)}</div>
    <div class="card-title">知识库</div>
    <div class="card-desc">搜索 · 浏览 · 手动录入</div>
</div>
""", unsafe_allow_html=True)
        st.markdown(
            f'<span style="font-size:0.75rem;color:#94A3B8;">{icon("inbox", 14)} {total_content} 条内容已归档</span>',
            unsafe_allow_html=True,
        )
        if st.button("进入知识库", key="home_to_kb", use_container_width=True):
            st.session_state.current_page = "knowledge"
            st.rerun()

    with nc3:
        st.markdown(f"""
<div class="nav-card">
    <div class="card-icon">{icon("bar-chart", 32)}</div>
    <div class="card-title">学习复盘</div>
    <div class="card-desc">进度 · 周报/月报 · AI 洞察</div>
</div>
""", unsafe_allow_html=True)
        st.markdown(
            f'<span style="font-size:0.75rem;color:#94A3B8;">{icon("flame", 14, color="#F87171")} 连续 {streak["current_streak"]} 天</span>',
            unsafe_allow_html=True,
        )
        if st.button("进入复盘", key="home_to_rv", use_container_width=True):
            st.session_state.current_page = "review"
            st.rerun()

    st.divider()

    st.markdown(
        f'{imd("target", "今日闭环状态", tag="h3", size=20)}',
        unsafe_allow_html=True,
    )

    ts1, ts2 = st.columns(2)
    with ts1:
        if unified:
            st.markdown(
                f'<div class="status-card done">{icon("check-square", 20, color="#4ADE80")} '
                f'<span>早报已就绪</span></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="status-card pending">{icon("clock", 20, color="#64748B")} '
                f'<span>早报待生成</span></div>',
                unsafe_allow_html=True,
            )
    with ts2:
        if quiz_done:
            st.markdown(
                f'<div class="status-card done">{icon("check-square", 20, color="#4ADE80")} '
                f'<span>测验已完成</span></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="status-card pending">{icon("clock", 20, color="#64748B")} '
                f'<span>测验待完成</span></div>',
                unsafe_allow_html=True,
            )

    if unified:
        st.divider()
        with st.expander("今日早报预览 (点击展开)", expanded=False):
            preview = unified["content"][:800]
            st.markdown(preview + "\n\n...")
            if st.button("阅读完整早报 →", key="home_preview_to_wb"):
                st.session_state.current_page = "workbench"
                st.rerun()


# =============================================
# RENDER CURRENT PAGE
# =============================================
page = st.session_state.current_page

if page == "home":
    render_home()
elif page == "workbench":
    render_workbench(db)
elif page == "knowledge":
    render_knowledge(db)
elif page == "review":
    render_review(db)
