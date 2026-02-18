# 🧠 AI Learning Hub — 统一 AI 学习平台

一个帮你系统性学习 AI 的自动化工具，整合三大学习模块：

- **🌐 GEO 学习** — Generative Engine Optimization，AI 搜索优化
- **📄 AI 前沿论文** — arXiv 论文追踪，产品经理视角解读
- **🎬 博主精选** — YouTube / Podcast / 小红书优质博主，产品 + AI 结合

每天自动抓取内容 → AI 生成学习简报 → 测验检测 → 周度/月度复盘，10 个月构建完整的 AI 知识体系。

---

## 快速开始

### 1. 安装依赖

```bash
cd ai-learning-hub
pip install -r requirements.txt
```

### 2. 配置 OpenAI API Key

```bash
export OPENAI_API_KEY='sk-your-api-key-here'
```

### 3. 启动 Web 版（推荐）

```bash
streamlit run app.py
```

### 3b. 或者使用终端版

```bash
python main.py daily              # GEO 每日学习
python main.py daily ai_papers    # AI 论文每日学习
python main.py daily creators     # 博主内容每日学习
```

---

## 核心功能

### Web 版 (`streamlit run app.py`)

| 页面 | 功能 |
|------|------|
| 🏠 Dashboard | 三模块学习进度总览、今日状态 |
| 🌐 GEO 学习 | 抓取 GEO 资讯 + AI 生成学习简报 |
| 📄 AI 论文 | arXiv 检索 + 论文速递 + 深度解读 |
| 🎬 博主精选 | YouTube/Podcast 自动抓取 + 小红书手动录入 + AI 摘要 |
| 📝 每日测验 | 多模块交互式答题 + 即时评分 |
| 📊 学习进度 | 跨模块数据可视化、成绩趋势 |
| 📈 周度总结 | 跨模块周度复盘报告 |
| 📅 月度总结 | 跨模块月度深度报告 |
| 🔍 知识库 | 跨模块搜索、浏览所有学习内容 |

### 终端版 (`python main.py`)

| 命令 | 功能 |
|------|------|
| `python main.py daily [module]` | 完整每日流程 |
| `python main.py fetch [module]` | 抓取最新内容 |
| `python main.py briefing [module]` | 生成今日简报 |
| `python main.py quiz [module]` | 今日测验 |
| `python main.py weekly` | 跨模块周度总结 |
| `python main.py monthly` | 跨模块月度总结 |
| `python main.py progress` | 学习进度 |
| `python main.py search <关键词>` | 搜索知识库 |

模块参数: `geo` / `ai_papers` / `creators`（默认 `geo`）

---

## 系统架构

```
ai-learning-hub/
├── config/
│   ├── settings.yaml           # 全局设置
│   ├── modules/
│   │   ├── geo.yaml            # GEO 模块源 + 关键词 + 学习路径
│   │   ├── ai_papers.yaml      # AI 论文模块
│   │   └── creators.yaml       # 博主内容模块
│   └── loader.py               # 配置加载器
├── scrapers/
│   ├── base_scraper.py         # 抓取器基类
│   ├── rss_scraper.py          # 通用 RSS 抓取
│   ├── youtube_scraper.py      # YouTube + Podcast 抓取
│   └── arxiv_scraper.py        # arXiv 论文检索
├── processors/
│   ├── content_processor.py    # 内容处理和过滤
│   └── transcript_processor.py # 视频/音频转录处理
├── generators/
│   ├── ai_engine.py            # OpenAI API 封装
│   ├── daily_briefing.py       # 多模块简报生成
│   ├── quiz_generator.py       # 多模块测验生成
│   └── summary_generator.py    # 跨模块周/月总结
├── tracker/
│   ├── database.py             # SQLite 数据库
│   └── progress.py             # 学习进度追踪
├── pages/                      # Streamlit 页面
├── data/                       # 数据存储
├── app.py                      # Web 主入口
├── main.py                     # CLI 主入口
└── requirements.txt
```

---

## 博主内容模块

### 自动抓取
- YouTube 频道 RSS + 字幕自动提取
- Podcast RSS 订阅

### 手动录入
- 小红书等无 API 平台的内容通过 Web 表单录入

### 防刷屏设计
- 每周固定消化 N 条精选内容
- 系统化数据库替代随意刷视频

### 配置博主频道

编辑 `config/modules/creators.yaml`，填入实际的频道 ID：

```yaml
youtube_channels:
  - name: "Lenny's Podcast"
    channel_id: "实际的频道ID"
    rss_url: "https://www.youtube.com/feeds/videos.xml?channel_id=实际ID"
```

---

## 10 个月学习路径

每个模块都有独立的 10 个月学习规划，通过 `config/modules/*.yaml` 配置。

---

## Tips

- **离线学习**: 所有内容保存为 Markdown 文件和 SQLite 数据库
- **数据安全**: 所有数据存储在本地，不上传
- **成本控制**: 默认使用 `gpt-4o-mini`（约 $0.01/天）
- **知识积累**: 跨模块标签化知识库，长期积累
