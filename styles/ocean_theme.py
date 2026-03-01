"""Living Nordic Summer — Dynamic cinematic glassmorphism theme for Streamlit."""


def get_ocean_css() -> str:
    return """<style>
/* ================================================
   GOOGLE FONTS
   ================================================ */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ================================================
   CSS VARIABLES
   ================================================ */
:root {
    --ocean-primary: #60A5FA;
    --ocean-secondary: #94A3B8;
    --ocean-deep: #1E3A8A;
    --sand-accent: #F4E2D8;
    --glass-bg: rgba(241, 245, 249, 0.08);
    --glass-bg-strong: rgba(241, 245, 249, 0.13);
    --glass-border: rgba(255, 255, 255, 0.12);
    --glass-border-strong: rgba(255, 255, 255, 0.20);
    --text-primary: #F1F5F9;
    --text-muted: #94A3B8;
    --text-dark: #F1F5F9;
    --text-light: #F1F5F9;
    --base-dark: #0F172A;
    --highlight-warm: rgba(255, 252, 230, 0.20);
    --highlight-warm-strong: rgba(255, 249, 224, 0.35);
}

/* ================================================
   PAGE TRANSITION — Smooth fade-in to avoid black flash
   ================================================ */
@keyframes pageIn {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0); }
}

html, body {
    background: #0F172A !important;
}

[data-testid="stMain"] {
    animation: pageIn 0.35s ease-out;
}

[data-testid="stSidebar"] {
    animation: pageIn 0.25s ease-out;
}

/* ================================================
   GLOBAL TYPOGRAPHY
   ================================================ */
*, *::before, *::after {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

/* ================================================
   GLOBAL BACKGROUND — Cinematic Ocean + Vignette + Mist
   ================================================ */
.stApp {
    background-image:
        radial-gradient(ellipse at 20% 50%, rgba(96,165,250,0.06) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 30%, rgba(148,163,184,0.04) 0%, transparent 50%),
        linear-gradient(to bottom, rgba(15,23,42,0.50), rgba(15,23,42,0.88)),
        url('https://images.unsplash.com/photo-1505228395891-9a51e7e86bf6?w=3840&q=80&auto=format&fit=crop') !important;
    background-size: cover !important;
    background-position: center !important;
    background-attachment: fixed !important;
    color: var(--text-primary);
    box-shadow: inset 0 0 180px 40px rgba(15, 23, 42, 0.45);
}

/* ================================================
   AMBIENT LAYER 1 — Palm Tree Silhouettes
   ================================================ */
.stApp::before {
    content: "";
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 0;
    background-image:
        url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 300'%3E%3Cpath d='M30 300 L35 180 Q20 140 5 120 Q25 135 40 130 Q20 100 10 70 Q30 95 50 95 Q40 60 35 30 Q50 65 65 75 Q60 45 65 20 Q68 55 78 70 Q85 40 95 25 Q88 60 85 80 Q100 60 115 55 Q95 80 90 95 Q115 80 130 80 Q105 95 95 110 Q120 100 140 105 Q110 115 95 125 Q105 140 100 160 L45 300Z' fill='rgba(15,23,42,0.85)' /%3E%3C/svg%3E"),
        url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 300'%3E%3Cpath d='M170 300 L165 190 Q180 150 195 130 Q175 145 160 140 Q180 110 190 80 Q170 105 150 105 Q160 70 165 40 Q150 75 135 85 Q140 55 135 30 Q132 65 122 80 Q115 50 105 35 Q112 70 115 90 Q100 70 85 65 Q105 90 110 105 Q85 90 70 90 Q95 105 105 120 Q80 110 60 115 Q90 125 105 135 Q95 150 100 170 L155 300Z' fill='rgba(15,23,42,0.75)' /%3E%3C/svg%3E");
    background-position: bottom left, bottom right;
    background-repeat: no-repeat, no-repeat;
    background-size: 180px auto, 160px auto;
    opacity: 0.14;
    transform-origin: bottom center;
    animation: palmSway 8s ease-in-out infinite alternate;
    will-change: transform;
}

@keyframes palmSway {
    0%   { transform: rotate(-0.4deg) translateX(-2px); }
    100% { transform: rotate(0.4deg) translateX(2px); }
}

/* ================================================
   AMBIENT LAYER 2 — Bokeh + Light Caustics + Streaks
   ================================================ */
.stApp::after {
    content: "";
    position: fixed;
    top: 0; left: 0;
    width: 100%; height: 100%;
    pointer-events: none;
    z-index: 0;
    background-image:
        radial-gradient(circle 80px at 12% 15%, rgba(255,252,230,0.09) 0%, transparent 70%),
        radial-gradient(circle 60px at 75% 10%, rgba(255,249,224,0.07) 0%, transparent 70%),
        radial-gradient(circle 100px at 85% 60%, rgba(96,165,250,0.05) 0%, transparent 70%),
        radial-gradient(circle 50px at 25% 70%, rgba(255,252,230,0.06) 0%, transparent 70%),
        radial-gradient(circle 70px at 50% 40%, rgba(96,165,250,0.04) 0%, transparent 70%),
        radial-gradient(circle 40px at 60% 85%, rgba(255,249,224,0.05) 0%, transparent 70%),
        linear-gradient(135deg, transparent 45%, rgba(255,252,230,0.03) 50%, transparent 55%);
    animation: bokehDrift 30s ease-in-out infinite alternate;
    will-change: transform, opacity;
}

@keyframes bokehDrift {
    0%   { opacity: 0.7; transform: translate(0, 0) scale(1); }
    33%  { opacity: 1;   transform: translate(10px, -6px) scale(1.02); }
    66%  { opacity: 0.8; transform: translate(-8px, 4px) scale(0.98); }
    100% { opacity: 0.9; transform: translate(5px, -3px) scale(1.01); }
}

/* ================================================
   WATER SHIMMER — applied on card surfaces
   ================================================ */
@keyframes waterShimmer {
    0%   { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}

/* ================================================
   SIDEBAR — Hide Streamlit auto-generated nav
   ================================================ */
[data-testid="stSidebarNav"] {
    display: none !important;
}

/* ================================================
   SIDEBAR — Dark Nordic Glass
   ================================================ */
[data-testid="stSidebar"] {
    background: rgba(15, 23, 42, 0.68) !important;
    backdrop-filter: blur(28px) saturate(120%) !important;
    -webkit-backdrop-filter: blur(28px) saturate(120%) !important;
    border-right: 1px solid rgba(255,255,255,0.07) !important;
    padding-top: 0.5rem !important;
}
[data-testid="stSidebar"] * {
    color: var(--text-primary) !important;
}
[data-testid="stSidebar"] .stMarkdown a {
    color: var(--ocean-primary) !important;
    transition: color 0.2s, text-shadow 0.2s;
}
[data-testid="stSidebar"] .stMarkdown a:hover {
    color: #93C5FD !important;
    text-shadow: 0 0 10px rgba(96,165,250,0.4);
}
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.06) !important;
    margin: 0.3rem 0 !important;
}
[data-testid="stSidebar"] [data-testid="stCaption"] {
    color: var(--text-muted) !important;
}

/* Sidebar — Brand area */
.sidebar-brand {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--text-primary);
    padding: 0.2rem 0;
}
.sidebar-brand svg { flex-shrink: 0; }
.sidebar-tagline {
    font-size: 0.72rem;
    color: var(--text-muted) !important;
    margin: 2px 0 0 0;
    line-height: 1.4;
}
.sidebar-spacer {
    height: 0.6rem;
}

/* Sidebar — Section labels */
.sidebar-section-label {
    font-size: 0.65rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #64748B !important;
    margin: 0 0 4px 2px !important;
}

/* Sidebar — Navigation buttons (page links) */
[data-testid="stSidebar"] .stPageLink a {
    color: var(--text-primary) !important;
    border-radius: 10px;
    padding: 0.45rem 0.7rem !important;
    font-size: 0.85rem;
    font-weight: 500;
    transition: background 0.25s, box-shadow 0.25s, transform 0.15s;
    border: 1px solid transparent;
}
[data-testid="stSidebar"] .stPageLink a:hover {
    background: rgba(96,165,250,0.10) !important;
    box-shadow: 0 0 12px rgba(96,165,250,0.10);
    transform: translateX(2px);
}
[data-testid="stSidebar"] .stPageLink a[aria-current="page"] {
    background: rgba(96,165,250,0.16) !important;
    border: 1px solid rgba(96,165,250,0.20);
    box-shadow: inset 3px 0 0 0 var(--ocean-primary), 0 0 10px rgba(96,165,250,0.08);
    font-weight: 600;
}

/* Sidebar — Checklist */
.sidebar-checklist {
    display: flex;
    flex-direction: column;
    gap: 6px;
    padding: 0 2px;
}
.sidebar-checklist .checklist-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.82rem;
    padding: 5px 8px;
    border-radius: 8px;
    transition: background 0.2s;
}
.sidebar-checklist .checklist-item.done {
    color: #4ADE80 !important;
}
.sidebar-checklist .checklist-item.done span {
    color: #94A3B8 !important;
    text-decoration: line-through;
    opacity: 0.7;
}
.sidebar-checklist .checklist-item.pending span {
    color: var(--text-primary) !important;
}

/* Sidebar — Tip box */
.sidebar-tip {
    background: rgba(96, 165, 250, 0.06);
    border: 1px solid rgba(96, 165, 250, 0.10);
    border-radius: 8px;
    padding: 8px 10px;
    font-size: 0.72rem;
    color: var(--text-muted);
    line-height: 1.5;
    margin-bottom: 16px;
}
.sidebar-tip b {
    color: var(--text-primary);
    font-weight: 500;
}
.sidebar-tip span {
    opacity: 0.8;
}

/* Sidebar — Icon Navigation Buttons */
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] .stButton button {
    width: 44px !important;
    height: 44px !important;
    min-width: 44px !important;
    padding: 0 !important;
    font-size: 1.2rem !important;
    border-radius: 12px !important;
    background: rgba(241, 245, 249, 0.06) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    transition: all 0.25s ease !important;
}
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] .stButton button:hover {
    background: rgba(96, 165, 250, 0.15) !important;
    border-color: rgba(96, 165, 250, 0.25) !important;
    transform: translateY(-2px);
}
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] .stButton button:active,
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] .stButton button:focus {
    background: rgba(96, 165, 250, 0.25) !important;
    border-color: rgba(96, 165, 250, 0.45) !important;
    box-shadow: 0 0 16px rgba(96, 165, 250, 0.35) !important;
}

/* Sidebar — Expander override (30-min flow) */
[data-testid="stSidebar"] [data-testid="stExpander"] {
    background: rgba(241,245,249,0.04) !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
    border-radius: 8px !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary {
    font-size: 0.78rem !important;
    font-weight: 500;
    color: var(--text-muted) !important;
}

/* ================================================
   HOMEPAGE — Status cards
   ================================================ */
.status-card {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0.8rem 1rem;
    border-radius: 12px;
    font-size: 0.9rem;
    font-weight: 500;
    transition: transform 0.2s;
}
.status-card.done {
    background: rgba(74, 222, 128, 0.08);
    border: 1px solid rgba(74, 222, 128, 0.15);
    color: #4ADE80;
}
.status-card.done span { color: var(--text-primary); }
.status-card.pending {
    background: rgba(100, 116, 139, 0.08);
    border: 1px solid rgba(100, 116, 139, 0.12);
    color: #64748B;
}
.status-card.pending span { color: var(--text-muted); }

/* ================================================
   HEADER — Transparent
   ================================================ */
[data-testid="stHeader"] {
    background: transparent !important;
}

/* ================================================
   MAIN CONTENT AREA
   ================================================ */
[data-testid="stMainBlockContainer"] {
    position: relative;
    z-index: 1;
}

/* ================================================
   NAVIGATION CARDS — Glass + Water Shimmer
   ================================================ */
.nav-card {
    background: var(--glass-bg) !important;
    backdrop-filter: blur(24px) saturate(110%);
    -webkit-backdrop-filter: blur(24px) saturate(110%);
    border: 1px solid var(--glass-border-strong) !important;
    border-radius: 16px !important;
    padding: 1.5rem 1.2rem;
    text-align: center;
    box-shadow: 0 8px 32px rgba(15, 23, 42, 0.25);
    transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
    position: relative;
    overflow: hidden;
}
.nav-card::before {
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg,
        transparent,
        var(--highlight-warm),
        rgba(255,255,255,0.15),
        var(--highlight-warm),
        transparent);
}
.nav-card::after {
    content: "";
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 100%;
    pointer-events: none;
    background: linear-gradient(105deg,
        transparent 40%,
        rgba(255,255,255,0.04) 44%,
        rgba(255,255,255,0.10) 50%,
        rgba(255,255,255,0.04) 56%,
        transparent 60%);
    background-size: 200% 100%;
    animation: waterShimmer 7s ease-in-out infinite;
}
.nav-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 16px 48px rgba(15, 23, 42, 0.35), 0 0 20px rgba(96,165,250,0.08);
    border-color: rgba(96,165,250,0.25) !important;
}
.nav-card .card-icon {
    font-size: 2rem;
    margin-bottom: 0.5rem;
    line-height: 1;
}
.nav-card .card-icon svg {
    width: 32px;
    height: 32px;
    stroke: var(--ocean-primary);
    opacity: 0.9;
}
.nav-card .card-title {
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-primary) !important;
    margin-bottom: 0.3rem;
    letter-spacing: -0.01em;
}
.nav-card .card-desc {
    font-size: 0.8rem;
    color: var(--text-muted) !important;
    line-height: 1.5;
}

/* ================================================
   GLASS CARD — generic
   ================================================ */
.glass-card {
    background: var(--glass-bg);
    backdrop-filter: blur(24px) saturate(110%);
    -webkit-backdrop-filter: blur(24px) saturate(110%);
    border: 1px solid var(--glass-border);
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 8px 32px rgba(15, 23, 42, 0.2);
    position: relative;
    overflow: hidden;
}
.glass-card::after {
    content: "";
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 100%;
    pointer-events: none;
    background: linear-gradient(105deg,
        transparent 40%,
        rgba(255,255,255,0.03) 44%,
        rgba(255,255,255,0.08) 50%,
        rgba(255,255,255,0.03) 56%,
        transparent 60%);
    background-size: 200% 100%;
    animation: waterShimmer 8s ease-in-out infinite;
}

/* ================================================
   TYPOGRAPHY — Premium Scale
   ================================================ */
.main-header {
    font-size: 1.5rem !important;
    font-weight: 600 !important;
    color: var(--text-primary) !important;
    -webkit-text-fill-color: var(--text-primary) !important;
    background: none !important;
    text-shadow: 0 2px 20px rgba(96, 165, 250, 0.15);
    margin-bottom: 0.3rem;
    letter-spacing: -0.02em;
    line-height: 1.3;
}
.sub-header {
    font-size: 0.875rem;
    color: var(--text-muted) !important;
    margin-bottom: 1.5rem;
    line-height: 1.6;
}

[data-testid="stMainBlockContainer"] .stMarkdown h1 {
    font-size: 1.5rem !important;
    font-weight: 600 !important;
    letter-spacing: -0.02em;
    line-height: 1.3;
    color: var(--text-primary) !important;
    text-shadow: 0 1px 12px rgba(96,165,250,0.10);
}
[data-testid="stMainBlockContainer"] .stMarkdown h2 {
    font-size: 1.125rem !important;
    font-weight: 500 !important;
    line-height: 1.4;
    color: var(--text-primary) !important;
    text-shadow: 0 1px 8px rgba(96,165,250,0.08);
}
[data-testid="stMainBlockContainer"] .stMarkdown h3 {
    font-size: 1rem !important;
    font-weight: 500 !important;
    line-height: 1.4;
    color: var(--text-primary) !important;
}
[data-testid="stMainBlockContainer"] .stMarkdown h4 {
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    color: var(--text-primary) !important;
}

[data-testid="stMainBlockContainer"] .stMarkdown p,
[data-testid="stMainBlockContainer"] .stMarkdown li,
[data-testid="stMainBlockContainer"] .stMarkdown td,
[data-testid="stMainBlockContainer"] .stMarkdown th {
    font-size: 0.875rem;
    line-height: 1.6;
    color: var(--text-primary) !important;
}
[data-testid="stMainBlockContainer"] .stMarkdown strong {
    color: #E2E8F0 !important;
}
[data-testid="stMainBlockContainer"] [data-testid="stCaption"] {
    font-size: 0.75rem !important;
    color: var(--text-muted) !important;
    opacity: 0.8;
}
[data-testid="stMainBlockContainer"] .stMarkdown a {
    color: var(--ocean-primary) !important;
}
[data-testid="stMainBlockContainer"] .stMarkdown blockquote {
    border-left: 3px solid var(--ocean-primary) !important;
    color: #CBD5E1 !important;
    padding-left: 1rem;
}
[data-testid="stMainBlockContainer"] .stMarkdown code {
    background: rgba(241,245,249,0.1) !important;
    color: #93C5FD !important;
    font-size: 0.8rem;
    padding: 2px 6px;
    border-radius: 4px;
}

/* Inline SVG icon alignment inside markdown */
[data-testid="stMainBlockContainer"] .stMarkdown svg.icon {
    vertical-align: middle;
    display: inline-block;
    margin-right: 4px;
}

/* ================================================
   STREAMLIT METRICS — Dark Glass
   ================================================ */
[data-testid="stMetric"] {
    background: var(--glass-bg) !important;
    backdrop-filter: blur(20px) saturate(110%);
    -webkit-backdrop-filter: blur(20px) saturate(110%);
    border: 1px solid var(--glass-border);
    border-radius: 12px;
    padding: 0.75rem 1rem;
    height: 95px !important;
    box-sizing: border-box !important;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 24px rgba(15,23,42,0.15);
}
[data-testid="stMetric"] label {
    color: var(--text-muted) !important;
    font-size: 0.75rem !important;
}
[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: var(--text-primary) !important;
    font-weight: 700;
    font-size: 1.25rem !important;
}
[data-testid="stMetric"] [data-testid="stMetricDelta"] {
    color: var(--text-muted) !important;
    font-size: 0.7rem !important;
}

/* ================================================
   EXPANDERS
   ================================================ */
[data-testid="stExpander"] {
    background: var(--glass-bg-strong) !important;
    backdrop-filter: blur(20px) saturate(110%);
    -webkit-backdrop-filter: blur(20px) saturate(110%);
    border: 1px solid var(--glass-border) !important;
    border-radius: 12px !important;
    overflow: hidden;
    transition: box-shadow 0.3s ease;
}
[data-testid="stExpander"]:hover {
    box-shadow: 0 4px 20px rgba(15,23,42,0.12);
}
[data-testid="stExpander"] summary {
    color: var(--text-primary) !important;
    font-size: 0.875rem;
    font-weight: 500;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}
[data-testid="stExpander"] summary * {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}
[data-testid="stExpander"] summary:hover {
    color: #93C5FD !important;
}
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] p {
    color: var(--text-primary) !important;
}
/* ================================================
   CONTENT CARDS — Replace expander with custom cards
   ================================================ */
.content-card {
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    border-radius: 10px;
    padding: 0.875rem 1rem;
    margin-bottom: 0.5rem;
    transition: background 0.2s, border-color 0.2s;
}
.content-card:hover {
    background: var(--glass-bg-strong);
    border-color: var(--glass-border-strong);
}
.content-card-header {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
}
.content-card-title {
    color: var(--text-primary);
    font-size: 0.9rem;
    font-weight: 500;
    line-height: 1.4;
}
.content-card-meta {
    color: var(--text-muted);
    font-size: 0.75rem;
    margin-top: 0.35rem;
}
.content-card-conclusion {
    color: var(--text-primary);
    font-size: 0.8rem;
    margin-top: 0.5rem;
    padding: 0.5rem;
    background: rgba(96, 165, 250, 0.08);
    border-radius: 6px;
    border-left: 2px solid var(--ocean-primary);
}
.content-card-tags {
    color: var(--text-muted);
    font-size: 0.72rem;
    margin-top: 0.4rem;
    display: flex;
    align-items: center;
    gap: 4px;
}

[data-testid="stExpander"] summary > span,
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] {
    color: var(--text-primary) !important;
    visibility: visible !important;
    opacity: 1 !important;
}
[data-testid="stExpander"] details summary {
    padding: 0.75rem 1rem !important;
    min-height: 40px !important;
}
[data-testid="stExpander"] details summary span[data-testid="stMarkdownContainer"],
[data-testid="stExpander"] details > summary > div {
    display: flex !important;
    align-items: center !important;
    color: var(--text-primary) !important;
}
[data-testid="stExpander"] details summary span[data-testid="stMarkdownContainer"] p {
    margin: 0 !important;
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    color: var(--text-primary) !important;
}

/* ================================================
   EXPANDER TOGGLE ICON — Hide Material Icon text leakage
   ================================================ */
[data-testid="stExpander"] details summary .material-symbols-rounded,
[data-testid="stExpander"] summary > span.material-symbols-rounded,
[data-testid="stExpander"] summary svg + span,
[data-testid="stExpander"] details > summary > span:first-child {
    font-size: 0 !important;
    color: transparent !important;
    -webkit-text-fill-color: transparent !important;
    overflow: hidden !important;
    width: 1.2em !important;
    display: inline-block !important;
}
[data-testid="stExpander"] details[open] > summary > span:first-child::before,
[data-testid="stExpander"] details:not([open]) > summary > span:first-child::before {
    content: "" !important;
    display: inline-block !important;
    width: 14px !important;
    height: 14px !important;
    vertical-align: middle !important;
    background-size: contain !important;
    background-repeat: no-repeat !important;
    background-position: center !important;
}
[data-testid="stExpander"] details:not([open]) > summary > span:first-child::before {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2394A3B8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M9 18l6-6-6-6'/%3E%3C/svg%3E") !important;
}
[data-testid="stExpander"] details[open] > summary > span:first-child::before {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2394A3B8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E") !important;
}

/* ================================================
   SIDEBAR COLLAPSE BUTTON FIX — Hide Material Icon text leakage
   ================================================ */
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"] {
    font-size: 0 !important;
    color: transparent !important;
    overflow: hidden !important;
}
[data-testid="stSidebarCollapseButton"] button,
[data-testid="collapsedControl"] button,
[data-testid="stSidebarCollapsedControl"] button {
    background: var(--glass-bg) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 8px !important;
    color: transparent !important;
    font-size: 0 !important;
    line-height: 0 !important;
    width: 32px !important;
    height: 32px !important;
    min-width: 32px !important;
    padding: 0 !important;
    position: relative !important;
    overflow: hidden !important;
}
[data-testid="stSidebarCollapseButton"] button span,
[data-testid="collapsedControl"] button span,
[data-testid="stSidebarCollapsedControl"] button span,
[data-testid="stSidebarCollapseButton"] button [data-testid],
[data-testid="collapsedControl"] button [data-testid],
[data-testid="stSidebarCollapsedControl"] button [data-testid],
[data-testid="stSidebarCollapseButton"] .material-symbols-rounded,
[data-testid="collapsedControl"] .material-symbols-rounded,
[data-testid="stSidebarCollapsedControl"] .material-symbols-rounded {
    font-size: 0 !important;
    color: transparent !important;
    -webkit-text-fill-color: transparent !important;
    visibility: hidden !important;
    width: 0 !important;
    height: 0 !important;
    overflow: hidden !important;
    position: absolute !important;
}
[data-testid="stSidebarCollapseButton"] button::before,
[data-testid="collapsedControl"] button::before,
[data-testid="stSidebarCollapsedControl"] button::before {
    content: "" !important;
    display: block !important;
    visibility: visible !important;
    width: 16px !important;
    height: 16px !important;
    position: absolute !important;
    top: 50% !important;
    left: 50% !important;
    transform: translate(-50%, -50%) !important;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2394A3B8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M15 18l-6-6 6-6'/%3E%3C/svg%3E");
    background-size: contain;
    background-repeat: no-repeat;
    background-position: center;
}
[data-testid="collapsedControl"] button::before,
[data-testid="stSidebarCollapsedControl"] button::before {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2394A3B8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M9 18l6-6-6-6'/%3E%3C/svg%3E") !important;
}
[data-testid="stSidebarCollapseButton"] button:hover,
[data-testid="collapsedControl"] button:hover,
[data-testid="stSidebarCollapsedControl"] button:hover {
    background: var(--glass-bg-strong) !important;
    border-color: var(--glass-border-strong) !important;
}
[data-testid="stSidebarCollapseButton"] button:hover::before,
[data-testid="collapsedControl"] button:hover::before,
[data-testid="stSidebarCollapsedControl"] button:hover::before {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23F1F5F9' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M15 18l-6-6 6-6'/%3E%3C/svg%3E") !important;
}
[data-testid="collapsedControl"] button:hover::before,
[data-testid="stSidebarCollapsedControl"] button:hover::before {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23F1F5F9' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M9 18l6-6-6-6'/%3E%3C/svg%3E") !important;
}

/* ================================================
   TABS — Glass with warm glow
   ================================================ */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(15, 23, 42, 0.35);
    border-radius: 10px;
    padding: 6px;
    gap: 12px;
    border: 1px solid rgba(255,255,255,0.06);
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--text-muted) !important;
    border-radius: 8px;
    font-weight: 500;
    font-size: 0.875rem;
    padding: 8px 16px !important;
    transition: background 0.25s, color 0.25s, box-shadow 0.25s;
}
.stTabs [data-baseweb="tab"]:hover {
    background: rgba(96,165,250,0.08) !important;
    color: var(--text-primary) !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(96,165,250,0.15) !important;
    color: var(--text-primary) !important;
    box-shadow: 0 0 16px rgba(96,165,250,0.12), 0 0 8px rgba(255,252,230,0.06);
    font-weight: 600;
}
.stTabs [data-baseweb="tab-highlight"] {
    background: linear-gradient(to right, var(--ocean-primary), var(--ocean-deep)) !important;
    height: 2px !important;
    border-radius: 1px;
}
.stTabs [data-baseweb="tab-panel"] {
    color: var(--text-primary) !important;
}

/* ================================================
   BUTTONS
   ================================================ */
.stButton > button {
    border-radius: 9999px !important;
    border: 1px solid rgba(255,255,255,0.10) !important;
    font-weight: 500;
    font-size: 0.875rem;
    color: var(--text-primary) !important;
    background: rgba(241,245,249,0.06) !important;
    padding: 0.5rem 1.2rem;
    transition: transform 0.2s ease, box-shadow 0.25s ease, background 0.25s ease, filter 0.25s ease;
}
.stButton > button[kind="primary"],
[data-testid="stFormSubmitButton"] > button,
[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg, #60A5FA, #1E3A8A) !important;
    color: var(--text-primary) !important;
    border: none !important;
    box-shadow: 0 4px 20px rgba(96, 165, 250, 0.25);
}
[data-testid="stFormSubmitButton"] > button:hover,
[data-testid="stFormSubmitButton"] button:hover {
    background: linear-gradient(135deg, #93C5FD, #2563EB) !important;
    box-shadow: 0 8px 32px rgba(96, 165, 250, 0.35);
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 0 24px rgba(96,165,250,0.20);
    background: rgba(96,165,250,0.12) !important;
    filter: brightness(1.05);
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #93C5FD, #2563EB) !important;
    box-shadow: 0 8px 32px rgba(96, 165, 250, 0.35);
    filter: brightness(1.05);
}

/* ================================================
   FORMS
   ================================================ */
[data-testid="stForm"] {
    background: var(--glass-bg-strong) !important;
    backdrop-filter: blur(20px) saturate(110%);
    -webkit-backdrop-filter: blur(20px) saturate(110%);
    border: 1px solid var(--glass-border) !important;
    border-radius: 16px !important;
    padding: 1.2rem;
}

/* ================================================
   TEXT INPUTS / TEXT AREAS / SELECTS — Glass Style
   ================================================ */
.stTextInput input,
.stTextArea textarea {
    background: rgba(241, 245, 249, 0.08) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(96, 165, 250, 0.20) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
    font-size: 0.875rem;
    transition: border-color 0.25s, box-shadow 0.25s, background 0.25s;
}
.stTextInput input:hover,
.stTextArea textarea:hover {
    background: rgba(241, 245, 249, 0.12) !important;
    border-color: rgba(96, 165, 250, 0.30) !important;
}
.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: #64748B !important;
}
.stTextInput input:focus,
.stTextArea textarea:focus {
    background: rgba(241, 245, 249, 0.10) !important;
    border-color: var(--ocean-primary) !important;
    box-shadow: 0 0 16px rgba(96, 165, 250, 0.25) !important;
    outline: none !important;
}

/* Selectbox / Multiselect — Glass Style */
.stSelectbox [data-baseweb="select"],
.stMultiSelect [data-baseweb="select"] {
    background: rgba(241, 245, 249, 0.08) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(96, 165, 250, 0.20) !important;
    border-radius: 10px !important;
    transition: border-color 0.25s, box-shadow 0.25s;
}
.stSelectbox [data-baseweb="select"]:hover,
.stMultiSelect [data-baseweb="select"]:hover {
    background: rgba(241, 245, 249, 0.12) !important;
    border-color: rgba(96, 165, 250, 0.30) !important;
}
.stSelectbox [data-baseweb="select"] > div,
.stMultiSelect [data-baseweb="select"] > div {
    background: transparent !important;
}
.stSelectbox [data-baseweb="select"] span,
.stMultiSelect [data-baseweb="select"] span {
    color: var(--text-primary) !important;
}
/* Dropdown menu */
[data-baseweb="popover"] > div,
[data-baseweb="menu"] {
    background: rgba(15, 23, 42, 0.95) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(96, 165, 250, 0.20) !important;
    border-radius: 10px !important;
}
[data-baseweb="menu"] li {
    color: var(--text-primary) !important;
    transition: background 0.2s;
}
[data-baseweb="menu"] li:hover {
    background: rgba(96, 165, 250, 0.15) !important;
}

/* ================================================
   RADIO — Glowing rings
   ================================================ */
.stRadio > div {
    color: var(--text-primary) !important;
}
.stRadio label {
    color: var(--text-primary) !important;
    font-size: 0.875rem;
    transition: color 0.2s;
}
.stRadio label:hover {
    color: #93C5FD !important;
}
.stRadio [data-testid="stMarkdownContainer"] {
    color: var(--text-primary) !important;
}
/* Style radio indicator */
.stRadio label > div:first-child {
    transition: box-shadow 0.3s ease, border-color 0.3s ease;
}
.stRadio label[data-checked="true"] > div:first-child,
.stRadio input[type="radio"]:checked + div {
    box-shadow: 0 0 10px rgba(96, 165, 250, 0.5) !important;
}

/* ================================================
   CHECKBOX — Glowing
   ================================================ */
.stCheckbox label {
    color: var(--text-primary) !important;
    font-size: 0.875rem;
    transition: color 0.2s;
}
.stCheckbox label:hover {
    color: #93C5FD !important;
}
.stCheckbox [data-checked="true"] {
    box-shadow: 0 0 8px rgba(96, 165, 250, 0.45);
}

/* ================================================
   DIVIDERS
   ================================================ */
[data-testid="stMainBlockContainer"] hr {
    border-color: rgba(255, 255, 255, 0.06) !important;
}

/* ================================================
   DATAFRAMES
   ================================================ */
[data-testid="stDataFrame"] {
    background: rgba(15, 23, 42, 0.30);
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.06);
}

/* ================================================
   ALERTS (info/success/warning/error)
   ================================================ */
[data-testid="stAlert"] {
    background: var(--glass-bg-strong) !important;
    backdrop-filter: blur(16px) saturate(110%);
    -webkit-backdrop-filter: blur(16px) saturate(110%);
    border: 1px solid var(--glass-border) !important;
    border-radius: 12px !important;
    color: var(--text-primary) !important;
}
[data-testid="stAlert"] p {
    color: var(--text-primary) !important;
    font-size: 0.875rem;
}

/* ================================================
   PROGRESS BAR
   ================================================ */
.stProgress > div > div {
    background: linear-gradient(to right, var(--ocean-primary), var(--ocean-deep)) !important;
    border-radius: 6px;
}

/* ================================================
   SPINNER
   ================================================ */
.stSpinner > div {
    color: var(--text-primary) !important;
}

/* ================================================
   PAGE LINK BUTTONS
   ================================================ */
.stPageLink a {
    background: rgba(96, 165, 250, 0.08) !important;
    border: 1px solid rgba(96, 165, 250, 0.15) !important;
    border-radius: 9999px !important;
    color: var(--text-primary) !important;
    font-size: 0.875rem;
    transition: background 0.25s, transform 0.2s ease, box-shadow 0.25s;
}
.stPageLink a:hover {
    background: rgba(96, 165, 250, 0.16) !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(96,165,250,0.15);
}

/* ================================================
   LINK BUTTONS
   ================================================ */
.stLinkButton a {
    background: rgba(96, 165, 250, 0.08) !important;
    border: 1px solid rgba(96, 165, 250, 0.15) !important;
    border-radius: 9999px !important;
    color: var(--ocean-primary) !important;
    font-size: 0.875rem;
}
.stLinkButton a:hover {
    background: rgba(96, 165, 250, 0.16) !important;
}

/* ================================================
   MODULE PILLS
   ================================================ */
.pill-geo {
    background: rgba(96, 165, 250, 0.15);
    color: var(--ocean-primary);
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 500;
}
.pill-paper {
    background: rgba(148, 163, 184, 0.15);
    color: #CBD5E1;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 500;
}
.pill-creator {
    background: rgba(244, 226, 216, 0.12);
    color: var(--sand-accent);
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 500;
}

/* Priority badges */
.badge-high {
    background: rgba(248, 113, 113, 0.15);
    color: #FCA5A5;
    padding: 1px 8px;
    border-radius: 8px;
    font-size: 0.7rem;
}
.badge-mid {
    background: rgba(251, 191, 36, 0.15);
    color: #FCD34D;
    padding: 1px 8px;
    border-radius: 8px;
    font-size: 0.7rem;
}

/* ================================================
   CHART CONTAINERS — Glass Style
   ================================================ */
[data-testid="stVegaLiteChart"],
[data-testid="stArrowVegaLiteChart"] {
    background: rgba(15, 23, 42, 0.40) !important;
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-radius: 12px;
    padding: 0.75rem;
    border: 1px solid rgba(96, 165, 250, 0.15);
    overflow: hidden;
}
/* Chart internal background */
[data-testid="stVegaLiteChart"] canvas,
[data-testid="stArrowVegaLiteChart"] canvas {
    background: transparent !important;
}
/* Vega-Lite SVG styling */
[data-testid="stVegaLiteChart"] svg,
[data-testid="stArrowVegaLiteChart"] svg {
    background: transparent !important;
}
/* Axis lines and grid */
[data-testid="stVegaLiteChart"] .vega-embed svg .mark-rule line,
[data-testid="stArrowVegaLiteChart"] .mark-rule line {
    stroke: rgba(255, 255, 255, 0.08) !important;
}
/* Axis labels */
[data-testid="stVegaLiteChart"] svg text,
[data-testid="stArrowVegaLiteChart"] svg text {
    fill: #94A3B8 !important;
    font-family: 'Inter', sans-serif !important;
}
/* Bar chart bars */
[data-testid="stVegaLiteChart"] .mark-rect rect,
[data-testid="stArrowVegaLiteChart"] .mark-rect rect {
    fill: #60A5FA !important;
    rx: 4;
    ry: 4;
}
/* Line chart lines */
[data-testid="stVegaLiteChart"] .mark-line path,
[data-testid="stArrowVegaLiteChart"] .mark-line path {
    stroke: #60A5FA !important;
}

/* ================================================
   ALERTS / INFO / SUCCESS / WARNING / ERROR — Glass
   ================================================ */
[data-testid="stAlert"] {
    background: rgba(15, 23, 42, 0.60) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(96, 165, 250, 0.20) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
}
[data-testid="stAlert"] p,
[data-testid="stAlert"] span {
    color: var(--text-primary) !important;
}
/* Info specific */
.stAlert[data-baseweb="notification"] {
    background: rgba(15, 23, 42, 0.60) !important;
}
div[data-testid="stNotification"] {
    background: rgba(15, 23, 42, 0.60) !important;
    backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(96, 165, 250, 0.20) !important;
    border-radius: 10px !important;
}
div[data-testid="stNotification"] p {
    color: var(--text-primary) !important;
}

/* ================================================
   MARKDOWN TABLES
   ================================================ */
[data-testid="stMainBlockContainer"] .stMarkdown table {
    border-collapse: collapse;
    width: 100%;
    font-size: 0.875rem;
}
[data-testid="stMainBlockContainer"] .stMarkdown table th {
    background: rgba(96,165,250,0.10) !important;
    color: var(--ocean-primary) !important;
    border-bottom: 1px solid rgba(255,255,255,0.10) !important;
    padding: 8px 12px;
    font-weight: 500;
    font-size: 0.8rem;
}
[data-testid="stMainBlockContainer"] .stMarkdown table td {
    border-bottom: 1px solid rgba(255,255,255,0.05) !important;
    padding: 8px 12px;
    color: var(--text-primary) !important;
}
[data-testid="stMainBlockContainer"] .stMarkdown table tr:hover td {
    background: rgba(96,165,250,0.05);
}

/* ================================================
   SCROLLBAR
   ================================================ */
::-webkit-scrollbar {
    width: 6px;
}
::-webkit-scrollbar-track {
    background: rgba(15, 23, 42, 0.2);
}
::-webkit-scrollbar-thumb {
    background: rgba(96, 165, 250, 0.20);
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(96, 165, 250, 0.35);
}

/* ================================================
   SELECTION HIGHLIGHT
   ================================================ */
::selection {
    background: rgba(96, 165, 250, 0.3);
    color: #FFFFFF;
}

/* ================================================
   BACKGROUND PARTICLE GRID — subtle moving dots
   ================================================ */
@keyframes particleMove {
    0%   { background-position: 0 0; }
    100% { background-position: 200px 200px; }
}

</style>"""
