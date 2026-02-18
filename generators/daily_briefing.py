"""每日早报生成器 - newsletter 风格，聚焦最新 idea"""

from datetime import datetime, date
from pathlib import Path

from config.loader import load_settings, load_module_config, get_data_path
from generators.ai_engine import AIEngine
from tracker.database import Database

MODULE_PROMPTS = {
    "geo": {
        "role": "GEO（Generative Engine Optimization）领域的资深分析师",
        "focus": "AI 搜索优化趋势、Generative Search 创新策略、行业格局变化",
        "domain": "GEO / AI 搜索优化",
        "tags_hint": "AI Search, SEO, GEO, LLM, Perplexity, SGE",
    },
    "ai_papers": {
        "role": "AI 前沿研究解读专家，擅长将学术论文翻译为产品经理可理解的语言",
        "focus": "最具突破性的技术进展、对产品和行业的潜在影响",
        "domain": "AI 前沿技术",
        "tags_hint": "LLM, Transformer, RLHF, Agent, Multimodal, RAG",
    },
    "creators": {
        "role": "产品经理 AI 学习教练，擅长从博主内容中提炼可落地的方法论",
        "focus": "最新的 AI 产品实践、工具用法、思维模型和可复用方法论",
        "domain": "产品经理 + AI",
        "tags_hint": "AI产品, 增长, 工具, 方法论, PMF, 用户体验",
    },
}


class DailyBriefingGenerator:
    """每日 AI 早报生成器 — newsletter 风格"""

    def __init__(self, db: Database = None, module: str = "geo"):
        self.db = db or Database()
        self.ai = AIEngine()
        self.module = module
        self.settings = load_settings()
        self.module_cfg = load_module_config(module)

    def generate(self, articles: list, target_date: str = None) -> str:
        if not target_date:
            target_date = date.today().isoformat()

        prompts = MODULE_PROMPTS.get(self.module, MODULE_PROMPTS["geo"])
        module_name = self.module_cfg.get("module_name", self.module)

        article_summaries = []
        for i, a in enumerate(articles, 1):
            article_summaries.append(
                f"[{i}] {a['title']}\n"
                f"来源: {a['source']} | "
                f"相关度: {a.get('relevance_score', 0):.1f}\n"
                f"摘要: {a.get('summary', '无摘要')}\n"
                f"链接: {a['url']}"
            )
        articles_text = "\n\n".join(article_summaries)

        system_prompt = (
            f"你是一位{prompts['role']}，同时也是一位优秀的 newsletter 作者。\n"
            f"你的任务是从今天抓取到的最新内容中，提炼最有价值的信息和洞察，"
            f"生成一份高质量的每日早报。\n\n"
            f"风格要求：\n"
            f"1. 使用中文输出，Markdown 格式\n"
            f"2. 像 Stratechery / The Information 那样——信息密度高、分析有深度、语言简洁有力\n"
            f"3. 从不同角度挑选内容，避免多条要点说同一件事\n"
            f"4. 每条要点必须标注来源和关键词标签\n"
            f"5. 不要布置任务，只提供信息、洞察和启发\n"
            f"6. 重点关注{prompts['focus']}"
        )

        user_prompt = f"""从以下 {len(articles)} 条最新内容中，提炼最有价值的信息。

📅 日期：{target_date}
常用标签参考：{prompts['tags_hint']}

---
今日抓取的内容：

{articles_text}

---

严格按照以下结构生成早报（每个 section 都必须包含）：

# ☀️ {module_name}早报 — {target_date}

---

### 🔥 今日核心速览
（挑选 3-5 条最重要的、来自不同角度的要点，每条格式如下：）

1. **[核心观点/事件一句话摘要]**
   - 来源: [网站/作者名] | 优先级: 高/中/低
   - 关键词标签: [从 {prompts['tags_hint']} 中选取相关标签]
   - 为什么重要: [一句话说明对{prompts['domain']}领域的价值]
   - 可落地启发: [一句话说明读完可以怎么思考或应用]

2. …（同上格式，确保每条来自不同来源/不同角度）

---

### 💡 深度解读
（选 2-3 个最有深度的内容，从不同角度解读，每条格式：）

- **角度 1: [观点或策略总结]**
  - 核心逻辑: [简述分析逻辑/数据/背景]
  - 可应用场景: [自己产品/业务/项目的类比启发]

- **角度 2: …**（同上，确保与角度1不同）

---

### 📡 趋势信号
（1-3 条值得持续关注的趋势方向）

- **[趋势描述]**
  - 来源/依据: [来源]
  - 学习价值: [为什么值得关注]
  - 潜在机会: [产品/策略/工具方向的启发]

---

### 🔗 推荐阅读

| 优先级 | 标题 | 来源 | 类型 | 标签 |
|--------|------|------|------|------|
| 高 | … | … | 文章/指南/博客 | … |
| 中 | … | … | … | … |

---

### 📝 今日金句
> [摘录一句最有启发性的核心观点或作者原话]
>
> 标签: [启发/策略/趋势]

---

### 💭 今日思考题
（1-2 个帮助内化的思考题，例如：这个策略如何应用到我现有的产品优化中？）"""

        briefing_content = self.ai.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=4000,
        )

        self.db.save_briefing(
            date_str=target_date,
            content=briefing_content,
            article_count=len(articles),
            month_theme="",
            module=self.module,
        )
        self._save_to_file(target_date, briefing_content)

        item_ids = [a["id"] for a in articles if "id" in a]
        if item_ids:
            self.db.mark_content_used(item_ids)

        return briefing_content

    def generate_no_articles(self, target_date: str = None) -> str:
        if not target_date:
            target_date = date.today().isoformat()

        prompts = MODULE_PROMPTS.get(self.module, MODULE_PROMPTS["geo"])
        module_name = self.module_cfg.get("module_name", self.module)

        system_prompt = (
            f"你是一位{prompts['role']}，同时也是一位优秀的 newsletter 作者。\n"
            f"今天没有抓取到新内容，但你需要分享一个{prompts['domain']}领域"
            f"最新、最值得关注的趋势或洞察。使用中文输出，Markdown 格式。"
        )

        user_prompt = f"""今天（{target_date}）没有抓取到新内容。

请分享一个{prompts['domain']}领域最近最值得关注的趋势，生成一份简短早报：

# ☀️ {module_name}早报 — {target_date}

---

### 💡 今日洞察
（分享一个最新的、有启发性的趋势或洞察：
- 这个趋势是什么
- 为什么现在值得关注
- 可以怎么思考和应用）

---

### 📡 趋势信号
（1-2 个值得持续关注的方向）

---

### 💭 今日思考题
（1-2 个延伸思考题）"""

        content = self.ai.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=2000,
        )

        self.db.save_briefing(
            target_date, content, 0, "", self.module
        )
        self._save_to_file(target_date, content)
        return content

    def generate_from_transcript(self, item: dict,
                                 target_date: str = None) -> str:
        """基于视频/播客转录文本生成学习材料（博主模块专用）"""
        if not target_date:
            target_date = date.today().isoformat()

        module_name = self.module_cfg.get("module_name", self.module)
        transcript = item.get("transcript", "") or item.get("content", "")
        transcript_preview = transcript[:4000]

        system_prompt = (
            "你是一位产品经理 AI 学习教练，擅长从视频/播客内容中提炼可落地的方法论。\n"
            "你的任务是将博主内容转化为高信息密度的洞察和启发。\n\n"
            "风格要求：\n"
            "1. 使用中文输出，Markdown 格式\n"
            "2. 只提炼最有价值的 idea，不要流水账\n"
            "3. 每个观点都标注可应用场景\n"
            "4. 不要布置任务，只提供信息和启发"
        )

        user_prompt = f"""请从以下视频/播客内容中提炼最有价值的洞察。

📺 标题：{item.get('title', '未知')}
👤 博主：{item.get('creator_name', '未知')}
📅 日期：{target_date}

---
转录内容：

{transcript_preview}

---

请按以下结构输出：

# 🎬 {item.get('title', '未知')}
**博主**: {item.get('creator_name', '未知')} | **日期**: {target_date}

---

### 💡 核心观点（3-5个）
（每个观点：一句话总结 + 为什么重要 + 可应用场景）

### 📡 趋势信号
（这期内容反映了什么趋势？值得持续关注吗？）

### 💭 延伸思考
（1-2 个帮助深化理解的思考题）

### 📝 金句摘录
（1-2 句最有启发性的话）"""

        content = self.ai.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=4000,
        )

        self.db.save_briefing(
            target_date, content, 1, "", self.module
        )
        self._save_to_file(target_date, content)
        return content

    def generate_unified(self, target_date: str = None) -> str:
        """生成跨模块统一早报 — 合并三模块高质量内容"""
        if not target_date:
            target_date = date.today().isoformat()

        from processors.content_processor import ContentProcessor

        all_items = []
        for mid in ["geo", "ai_papers", "creators"]:
            proc = ContentProcessor(self.db, module=mid)
            items = proc.get_daily_articles()
            for item in items:
                item["_module"] = mid
            all_items.extend(items)

        all_items.sort(
            key=lambda x: (
                x.get("ai_quality_score", 0) * 0.6
                + x.get("relevance_score", 0) * 0.4
            ),
            reverse=True,
        )

        top_items = all_items[:15]

        if not top_items:
            return self.generate_no_articles(target_date)

        sections = {"geo": [], "ai_papers": [], "creators": []}
        for item in top_items:
            mod = item.get("_module", "geo")
            sections.setdefault(mod, []).append(item)

        items_text_parts = []
        mod_labels = {
            "geo": "GEO 资讯", "ai_papers": "AI 论文",
            "creators": "博主/Twitter",
        }
        for mod, label in mod_labels.items():
            items_in_mod = sections.get(mod, [])
            if not items_in_mod:
                continue
            items_text_parts.append(f"\n--- [{label}] ---")
            for i, item in enumerate(items_in_mod, 1):
                conclusion = item.get("core_conclusion", "")
                insight = item.get("actionable_insight", "")
                qs = item.get("ai_quality_score", 0)
                items_text_parts.append(
                    f"[{i}] {item['title']}\n"
                    f"来源: {item['source']} | 模块: {label} | "
                    f"质量分: {qs:.1f} | 相关度: {item.get('relevance_score', 0):.1f}\n"
                    f"摘要: {item.get('summary', '')[:300]}\n"
                    f"核心结论: {conclusion}\n"
                    f"可落地启发: {insight}\n"
                    f"链接: {item['url']}"
                )

        items_text = "\n\n".join(items_text_parts)

        system_prompt = (
            "你是一位顶级 AI 行业分析师和 newsletter 作者。\n"
            "你的任务是将来自三个模块（GEO 资讯、AI 论文、博主/Twitter）"
            "的最新内容合并为一份高质量的每日统一早报。\n\n"
            "风格要求：\n"
            "1. 使用中文输出，Markdown 格式\n"
            "2. 像 Stratechery / The Information / Morning Brew 那样——"
            "信息密度高、分析有深度、语言简洁有力\n"
            "3. 跨源趋势检测：如果多个独立来源提到同一话题，这是重要趋势信号\n"
            "4. 每条要点标注来源、标签和优先级\n"
            "5. 不要布置任务，只提供信息、洞察和启发"
        )

        user_prompt = f"""请将以下跨模块内容合并为统一的每日早报。

📅 日期：{target_date}
📊 今日内容：GEO {len(sections.get('geo', []))} 条 | 论文 {len(sections.get('ai_papers', []))} 条 | 博主/Twitter {len(sections.get('creators', []))} 条

---
{items_text}
---

严格按照以下结构生成统一早报：

# ☀️ AI Learning Hub 每日早报 — {target_date}

---

### 🔥 今日核心速览
（从所有模块中挑选 3-5 条最重要的，按优先级排序，每条格式：）

1. **[核心观点/事件]**
   - 来源: [来源] | 模块: [GEO/论文/博主] | 优先级: 高/中
   - 标签: [关键词标签]
   - 为什么重要: [一句话]
   - 可落地启发: [一句话]

---

### 💡 深度解读
（从不同模块各选 1 个最有深度的内容解读）

- **[GEO 角度]**: ...
  - 核心逻辑 + 可应用场景

- **[论文角度]**: ...
  - 核心逻辑 + 可应用场景

- **[博主洞察]**: ...
  - 核心逻辑 + 可应用场景

---

### 📡 趋势信号
（跨源趋势检测：哪些话题被 2+ 个独立来源同时提到？有什么新概念首次出现？）

- **[趋势 1]**
  - 被提及来源: [列出]
  - 信号强度: 强/中/弱
  - 潜在机会: [产品/策略启发]

---

### 🔗 推荐阅读

| 优先级 | 标题 | 来源 | 模块 | 标签 |
|--------|------|------|------|------|
| 高 | ... | ... | ... | ... |

---

### 📝 今日金句
> [一句最有启发性的话]
>
> 标签: [启发/策略/趋势]

---

### 💭 今日思考题
（1-2 个跨模块的思考题）"""

        content = self.ai.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=4000,
        )

        self.db.save_briefing(
            date_str=target_date,
            content=content,
            article_count=len(top_items),
            month_theme="",
            module="unified",
        )

        briefings_dir = get_data_path("briefings")
        unified_dir = briefings_dir / "unified" / target_date[:7]
        unified_dir.mkdir(parents=True, exist_ok=True)
        (unified_dir / f"briefing-{target_date}.md").write_text(
            content, encoding="utf-8"
        )

        item_ids = [a["id"] for a in top_items if "id" in a]
        if item_ids:
            self.db.mark_content_used(item_ids)

        return content

    def _save_to_file(self, date_str: str, content: str):
        briefings_dir = get_data_path("briefings")
        module_dir = briefings_dir / self.module / date_str[:7]
        module_dir.mkdir(parents=True, exist_ok=True)
        filepath = module_dir / f"briefing-{date_str}.md"
        filepath.write_text(content, encoding="utf-8")
        return filepath
