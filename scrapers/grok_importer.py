"""Grok 简报导入器 — 解析 Grok 输出的 Markdown 简报，转为标准 content_items"""

import re
from datetime import date

from scrapers.base_scraper import BaseScraper

SECTION_MODULE_MAP = {
    "ai 搜索": "geo",
    "geo": "geo",
    "ai 产品": "ai_product",
    "产品": "ai_product",
    "pm": "ai_product",
    "vibe coding": "ai_product",
    "ai 工具": "ai_product",
    "工具": "ai_product",
    "ai 技术": "ai_tech",
    "技术前沿": "ai_tech",
    "技术": "ai_tech",
    "ai 行业": "ai_tech",
    "行业动态": "ai_tech",
    "行业": "ai_tech",
}

SECTION_CATEGORY_MAP = {
    "geo": "grok_geo",
    "ai_product": "grok_product",
    "ai_tech": "grok_tech",
}


def _detect_module(section_title: str) -> str:
    """根据 section 标题匹配系统模块"""
    title_lower = section_title.lower().strip()
    for keyword, module in SECTION_MODULE_MAP.items():
        if keyword in title_lower:
            return module
    return "ai_tech"


def _extract_urls(text: str) -> list:
    """从文本中提取所有 URL"""
    return re.findall(r'https?://[^\s\)）\]】"\'<>]+', text)


def _parse_items_from_section(section_text: str, module: str, category: str,
                               today_str: str) -> list:
    """解析一个 section 内的编号条目"""
    item_pattern = re.compile(
        r'^\s*(\d+)\.\s+(.+?)$',
        re.MULTILINE,
    )

    matches = list(item_pattern.finditer(section_text))
    if not matches:
        return []

    items = []
    for i, match in enumerate(matches):
        title = match.group(2).strip()
        body_start = match.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(section_text)
        body = section_text[body_start:body_end].strip()

        creator = ""
        creator_match = re.search(r'发布者\s*[\(（]?\s*@?([^\)）·\n]+)', body)
        if creator_match:
            creator = creator_match.group(1).strip()

        urls = _extract_urls(body)
        url = urls[0] if urls else ""

        if not url:
            url = f"grok://{module}/{today_str}/{i+1}"

        body_lines = body.split('\n')
        summary_lines = []
        for line in body_lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            if line_stripped.startswith('发布者') and len(summary_lines) == 0:
                continue
            summary_lines.append(line_stripped)
        summary = ' '.join(summary_lines)

        item = BaseScraper.make_content_item(
            module=module,
            content_type="note",
            title=title,
            url=url,
            source=f"Grok/{creator}" if creator else "Grok",
            platform="grok",
            category=category,
            summary=summary[:500],
            content=summary,
            creator_name=creator,
            published_at=today_str,
            tags="Grok, X/Twitter",
            relevance_score=0.7,
        )
        items.append(item)

    return items


def parse_grok_markdown(markdown_text: str) -> dict:
    """解析完整的 Grok Markdown 简报。

    Returns:
        dict with keys:
            - items: list of content_item dicts
            - date: str (解析到的日期或今天)
            - highlight: str (今日一句话)
            - stats_line: str (统计行原文)
            - section_counts: dict (每个模块的条目数)
    """
    today_str = date.today().isoformat()

    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', markdown_text)
    if date_match:
        today_str = date_match.group(1)

    highlight = ""
    hl_match = re.search(r'📌\s*今日一句话[：:]\s*(.+?)(?:\n|$)', markdown_text)
    if hl_match:
        highlight = hl_match.group(1).strip()

    stats_line = ""
    stats_match = re.search(r'📈\s*统计[：:](.+?)(?:\n|$)', markdown_text)
    if stats_match:
        stats_line = stats_match.group(1).strip()

    section_pattern = re.compile(
        r'^[#\s]*[\U0001F300-\U0001FAFF\u2600-\u27BF]\s*(.+?)$',
        re.MULTILINE,
    )
    section_matches = list(section_pattern.finditer(markdown_text))

    all_items = []
    section_counts = {}

    for i, sec_match in enumerate(section_matches):
        sec_title = sec_match.group(1).strip()

        if any(skip in sec_title for skip in ['今日一句话', '统计', '情报简报']):
            continue

        module = _detect_module(sec_title)
        category = SECTION_CATEGORY_MAP.get(module, "grok")

        sec_start = sec_match.end()
        sec_end = section_matches[i + 1].start() if i + 1 < len(section_matches) else len(markdown_text)
        sec_body = markdown_text[sec_start:sec_end]

        if '今日无重要动态' in sec_body or '无重要动态' in sec_body:
            continue

        items = _parse_items_from_section(sec_body, module, category, today_str)
        all_items.extend(items)
        section_counts[module] = section_counts.get(module, 0) + len(items)

    return {
        "items": all_items,
        "date": today_str,
        "highlight": highlight,
        "stats_line": stats_line,
        "section_counts": section_counts,
    }
