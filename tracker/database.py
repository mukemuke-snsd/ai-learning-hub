"""数据库管理 - 统一的多模块 SQLite 存储"""

import sqlite3
from datetime import datetime, date
from pathlib import Path
from typing import Optional

from config.loader import get_db_path


class Database:
    """AI Learning Hub 统一数据库"""

    def __init__(self, db_path: Optional[Path] = None,
                 check_same_thread: bool = True):
        self.db_path = db_path or get_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(
            str(self.db_path), check_same_thread=check_same_thread
        )
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self):
        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module TEXT NOT NULL,
                content_type TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                source TEXT NOT NULL,
                platform TEXT,
                category TEXT,
                summary TEXT,
                content TEXT,
                transcript TEXT,
                relevance_score REAL DEFAULT 0,
                creator_name TEXT,
                duration_seconds INTEGER,
                published_at TEXT,
                fetched_at TEXT NOT NULL,
                used_in_briefing INTEGER DEFAULT 0,
                tags TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS creators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                platform TEXT NOT NULL,
                channel_url TEXT,
                rss_url TEXT,
                focus_area TEXT,
                notes TEXT,
                active INTEGER DEFAULT 1,
                added_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS briefings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module TEXT NOT NULL DEFAULT 'geo',
                date TEXT NOT NULL,
                content TEXT NOT NULL,
                article_count INTEGER,
                month_theme TEXT,
                created_at TEXT NOT NULL,
                UNIQUE(module, date)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quizzes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module TEXT NOT NULL DEFAULT 'geo',
                date TEXT NOT NULL,
                questions TEXT NOT NULL,
                answers TEXT,
                score REAL,
                completed INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module TEXT NOT NULL DEFAULT 'geo',
                date TEXT NOT NULL,
                activity_type TEXT NOT NULL,
                duration_minutes INTEGER,
                notes TEXT,
                created_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weekly_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module TEXT NOT NULL DEFAULT 'all',
                week_number INTEGER NOT NULL,
                year INTEGER NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                content TEXT NOT NULL,
                key_insights TEXT,
                created_at TEXT NOT NULL,
                UNIQUE(module, week_number, year)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS monthly_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module TEXT NOT NULL DEFAULT 'all',
                month INTEGER NOT NULL,
                year INTEGER NOT NULL,
                content TEXT NOT NULL,
                month_theme TEXT,
                key_learnings TEXT,
                created_at TEXT NOT NULL,
                UNIQUE(module, month, year)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_base (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module TEXT NOT NULL DEFAULT 'geo',
                topic TEXT NOT NULL,
                category TEXT,
                content TEXT NOT NULL,
                source_articles TEXT,
                tags TEXT,
                cross_modules TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        self.conn.commit()
        self._migrate()

    def _migrate(self):
        """Add columns that may not exist in older databases."""
        cursor = self.conn.cursor()
        existing = {
            row[1]
            for row in cursor.execute("PRAGMA table_info(content_items)")
        }
        migrations = {
            "core_conclusion": "TEXT DEFAULT ''",
            "actionable_insight": "TEXT DEFAULT ''",
            "ai_quality_score": "REAL DEFAULT 0",
        }
        for col, typedef in migrations.items():
            if col not in existing:
                cursor.execute(
                    f"ALTER TABLE content_items ADD COLUMN {col} {typedef}"
                )
        self.conn.commit()

    # === 内容条目操作 ===

    def save_content_item(self, item: dict) -> bool:
        try:
            self.conn.execute("""
                INSERT OR IGNORE INTO content_items
                (module, content_type, title, url, source, platform, category,
                 summary, content, transcript, relevance_score, creator_name,
                 duration_seconds, published_at, fetched_at, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.get("module", "geo"),
                item.get("content_type", "article"),
                item["title"],
                item["url"],
                item["source"],
                item.get("platform", "rss"),
                item.get("category", ""),
                item.get("summary", ""),
                item.get("content", ""),
                item.get("transcript", ""),
                item.get("relevance_score", 0),
                item.get("creator_name", ""),
                item.get("duration_seconds"),
                item.get("published_at", ""),
                datetime.now().isoformat(),
                item.get("tags", ""),
            ))
            self.conn.commit()
            return self.conn.total_changes > 0
        except sqlite3.Error:
            return False

    # 兼容旧接口
    def save_article(self, article: dict) -> bool:
        article.setdefault("module", "geo")
        article.setdefault("content_type", "article")
        article.setdefault("platform", "rss")
        return self.save_content_item(article)

    def get_unused_content(self, module: str = "geo", limit: int = 15,
                           min_score: float = 0.3) -> list:
        cursor = self.conn.execute("""
            SELECT * FROM content_items
            WHERE module = ? AND used_in_briefing = 0
                  AND relevance_score >= ?
            ORDER BY relevance_score DESC, published_at DESC
            LIMIT ?
        """, (module, min_score, limit))
        return [dict(row) for row in cursor.fetchall()]

    # 兼容旧接口
    def get_unused_articles(self, limit: int = 15,
                            min_score: float = 0.3) -> list:
        return self.get_unused_content("geo", limit, min_score)

    def update_enrichment(self, item_id: int, core_conclusion: str,
                          actionable_insight: str, ai_quality_score: float):
        self.conn.execute("""
            UPDATE content_items
            SET core_conclusion = ?, actionable_insight = ?,
                ai_quality_score = ?
            WHERE id = ?
        """, (core_conclusion, actionable_insight, ai_quality_score, item_id))
        self.conn.commit()

    def get_unenriched_content(self, module: str = None,
                                limit: int = 20) -> list:
        if module:
            cursor = self.conn.execute("""
                SELECT * FROM content_items
                WHERE ai_quality_score = 0 AND module = ?
                ORDER BY relevance_score DESC LIMIT ?
            """, (module, limit))
        else:
            cursor = self.conn.execute("""
                SELECT * FROM content_items
                WHERE ai_quality_score = 0
                ORDER BY relevance_score DESC LIMIT ?
            """, (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def mark_content_used(self, item_ids: list):
        if not item_ids:
            return
        placeholders = ",".join(["?" for _ in item_ids])
        self.conn.execute(
            f"UPDATE content_items SET used_in_briefing = 1 "
            f"WHERE id IN ({placeholders})",
            item_ids
        )
        self.conn.commit()

    def mark_articles_used(self, article_ids: list):
        self.mark_content_used(article_ids)

    def get_content_by_date_range(self, start_date: str, end_date: str,
                                  module: str = None) -> list:
        if module:
            cursor = self.conn.execute("""
                SELECT * FROM content_items
                WHERE fetched_at >= ? AND fetched_at <= ? AND module = ?
                ORDER BY relevance_score DESC
            """, (start_date, end_date, module))
        else:
            cursor = self.conn.execute("""
                SELECT * FROM content_items
                WHERE fetched_at >= ? AND fetched_at <= ?
                ORDER BY relevance_score DESC
            """, (start_date, end_date))
        return [dict(row) for row in cursor.fetchall()]

    def get_articles_by_date_range(self, start_date: str,
                                   end_date: str) -> list:
        return self.get_content_by_date_range(start_date, end_date, "geo")

    def get_content_by_module(self, module: str, limit: int = 50) -> list:
        cursor = self.conn.execute("""
            SELECT * FROM content_items WHERE module = ?
            ORDER BY fetched_at DESC LIMIT ?
        """, (module, limit))
        return [dict(row) for row in cursor.fetchall()]

    # === 创作者管理 ===

    def save_creator(self, creator: dict) -> int:
        cursor = self.conn.execute("""
            INSERT INTO creators
            (name, platform, channel_url, rss_url, focus_area, notes, added_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            creator["name"],
            creator["platform"],
            creator.get("channel_url", ""),
            creator.get("rss_url", ""),
            creator.get("focus_area", ""),
            creator.get("notes", ""),
            datetime.now().isoformat(),
        ))
        self.conn.commit()
        return cursor.lastrowid

    def get_creators(self, platform: str = None) -> list:
        if platform:
            cursor = self.conn.execute(
                "SELECT * FROM creators WHERE platform = ? AND active = 1",
                (platform,)
            )
        else:
            cursor = self.conn.execute(
                "SELECT * FROM creators WHERE active = 1"
            )
        return [dict(row) for row in cursor.fetchall()]

    # === 简报操作 ===

    def save_briefing(self, date_str: str, content: str, article_count: int,
                      month_theme: str = "", module: str = "geo"):
        self.conn.execute("""
            INSERT OR REPLACE INTO briefings
            (module, date, content, article_count, month_theme, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (module, date_str, content, article_count, month_theme,
              datetime.now().isoformat()))
        self.conn.commit()

    def get_briefing(self, date_str: str,
                     module: str = "geo") -> Optional[dict]:
        cursor = self.conn.execute(
            "SELECT * FROM briefings WHERE date = ? AND module = ?",
            (date_str, module)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_briefings_by_range(self, start_date: str, end_date: str,
                               module: str = None) -> list:
        if module:
            cursor = self.conn.execute("""
                SELECT * FROM briefings
                WHERE date >= ? AND date <= ? AND module = ?
                ORDER BY date
            """, (start_date, end_date, module))
        else:
            cursor = self.conn.execute("""
                SELECT * FROM briefings
                WHERE date >= ? AND date <= ?
                ORDER BY date
            """, (start_date, end_date))
        return [dict(row) for row in cursor.fetchall()]

    # === 测验操作 ===

    def save_quiz(self, date_str: str, questions: str,
                  module: str = "geo") -> int:
        cursor = self.conn.execute("""
            INSERT INTO quizzes (module, date, questions, created_at)
            VALUES (?, ?, ?, ?)
        """, (module, date_str, questions, datetime.now().isoformat()))
        self.conn.commit()
        return cursor.lastrowid

    def save_quiz_result(self, quiz_id: int, answers: str, score: float):
        self.conn.execute("""
            UPDATE quizzes SET answers = ?, score = ?, completed = 1
            WHERE id = ?
        """, (answers, score, quiz_id))
        self.conn.commit()

    def get_quiz(self, date_str: str,
                 module: str = "geo") -> Optional[dict]:
        cursor = self.conn.execute(
            "SELECT * FROM quizzes WHERE date = ? AND module = ? "
            "ORDER BY id DESC LIMIT 1",
            (date_str, module)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_quiz_scores(self, start_date: str, end_date: str,
                        module: str = None) -> list:
        if module:
            cursor = self.conn.execute("""
                SELECT date, score, module FROM quizzes
                WHERE date >= ? AND date <= ? AND completed = 1
                      AND module = ?
                ORDER BY date
            """, (start_date, end_date, module))
        else:
            cursor = self.conn.execute("""
                SELECT date, score, module FROM quizzes
                WHERE date >= ? AND date <= ? AND completed = 1
                ORDER BY date
            """, (start_date, end_date))
        return [dict(row) for row in cursor.fetchall()]

    # === 学习记录 ===

    def log_activity(self, activity_type: str, duration_minutes: int = 0,
                     notes: str = "", module: str = "geo"):
        self.conn.execute("""
            INSERT INTO learning_log
            (module, date, activity_type, duration_minutes, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (module, date.today().isoformat(), activity_type,
              duration_minutes, notes, datetime.now().isoformat()))
        self.conn.commit()

    def get_learning_stats(self, start_date: str, end_date: str,
                           module: str = None) -> dict:
        if module:
            cursor = self.conn.execute("""
                SELECT
                    COUNT(DISTINCT date) as active_days,
                    SUM(duration_minutes) as total_minutes,
                    COUNT(*) as total_activities
                FROM learning_log
                WHERE date >= ? AND date <= ? AND module = ?
            """, (start_date, end_date, module))
        else:
            cursor = self.conn.execute("""
                SELECT
                    COUNT(DISTINCT date) as active_days,
                    SUM(duration_minutes) as total_minutes,
                    COUNT(*) as total_activities
                FROM learning_log
                WHERE date >= ? AND date <= ?
            """, (start_date, end_date))
        row = cursor.fetchone()
        return dict(row) if row else {}

    # === 周报/月报 ===

    def save_weekly_report(self, week_number: int, year: int,
                           start_date: str, end_date: str,
                           content: str, key_insights: str = "",
                           module: str = "all"):
        self.conn.execute("""
            INSERT OR REPLACE INTO weekly_reports
            (module, week_number, year, start_date, end_date, content,
             key_insights, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (module, week_number, year, start_date, end_date, content,
              key_insights, datetime.now().isoformat()))
        self.conn.commit()

    def save_monthly_report(self, month: int, year: int, content: str,
                            month_theme: str = "", key_learnings: str = "",
                            module: str = "all"):
        self.conn.execute("""
            INSERT OR REPLACE INTO monthly_reports
            (module, month, year, content, month_theme, key_learnings,
             created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (module, month, year, content, month_theme, key_learnings,
              datetime.now().isoformat()))
        self.conn.commit()

    # === 知识库 ===

    def save_knowledge(self, topic: str, category: str, content: str,
                       source_articles: str = "", tags: str = "",
                       module: str = "geo", cross_modules: str = ""):
        now = datetime.now().isoformat()
        self.conn.execute("""
            INSERT INTO knowledge_base
            (module, topic, category, content, source_articles, tags,
             cross_modules, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (module, topic, category, content, source_articles, tags,
              cross_modules, now, now))
        self.conn.commit()

    def search_knowledge(self, keyword: str, module: str = None) -> list:
        if module:
            cursor = self.conn.execute("""
                SELECT * FROM knowledge_base
                WHERE (topic LIKE ? OR content LIKE ? OR tags LIKE ?
                       OR cross_modules LIKE ?)
                      AND module = ?
                ORDER BY updated_at DESC
            """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%",
                  f"%{keyword}%", module))
        else:
            cursor = self.conn.execute("""
                SELECT * FROM knowledge_base
                WHERE topic LIKE ? OR content LIKE ? OR tags LIKE ?
                      OR cross_modules LIKE ?
                ORDER BY updated_at DESC
            """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%",
                  f"%{keyword}%"))
        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
