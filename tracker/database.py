"""数据库管理 - 支持 SQLite（本地）和 PostgreSQL（Supabase 云端）双模式"""

import sqlite3
from datetime import datetime, date
from pathlib import Path
from typing import Optional

from config.loader import get_db_path, get_database_url

try:
    import psycopg2
    import psycopg2.extras
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False


class Database:
    """AI Learning Hub 统一数据库（自动检测 SQLite / Postgres）"""

    def __init__(self, db_path: Optional[Path] = None,
                 check_same_thread: bool = True):
        self.database_url = get_database_url()
        self.use_postgres = bool(self.database_url)

        if self.use_postgres:
            if not HAS_PSYCOPG2:
                raise ImportError(
                    "psycopg2 is required for Postgres. "
                    "Install with: pip install psycopg2-binary"
                )
            self.conn = psycopg2.connect(self.database_url)
            self.conn.autocommit = False
        else:
            self.db_path = db_path or get_db_path()
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.conn = sqlite3.connect(
                str(self.db_path), check_same_thread=check_same_thread
            )
            self.conn.row_factory = sqlite3.Row

        self._init_tables()

    def _ph(self, count: int = 1) -> str:
        """返回占位符：Postgres 用 %s，SQLite 用 ?"""
        placeholder = "%s" if self.use_postgres else "?"
        return ", ".join([placeholder] * count)

    def _execute(self, sql: str, params: tuple = ()):
        """执行 SQL，自动处理游标类型。Postgres 模式下自动恢复失败事务。"""
        if self.use_postgres:
            try:
                cursor = self.conn.cursor(
                    cursor_factory=psycopg2.extras.RealDictCursor
                )
                cursor.execute(sql, params)
                return cursor
            except Exception:
                self.conn.rollback()
                cursor = self.conn.cursor(
                    cursor_factory=psycopg2.extras.RealDictCursor
                )
                cursor.execute(sql, params)
                return cursor
        else:
            cursor = self.conn.cursor()
            cursor.execute(sql, params)
            return cursor

    def _fetchall_as_dicts(self, cursor) -> list:
        """将查询结果转为字典列表"""
        rows = cursor.fetchall()
        if self.use_postgres:
            return [dict(row) for row in rows]
        else:
            return [dict(row) for row in rows]

    def _fetchone_as_dict(self, cursor) -> Optional[dict]:
        """将单行结果转为字典"""
        row = cursor.fetchone()
        if row is None:
            return None
        return dict(row)

    def _init_tables(self):
        if self.use_postgres:
            self._init_tables_postgres()
        else:
            self._init_tables_sqlite()

    def _init_tables_sqlite(self):
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
                tags TEXT,
                core_conclusion TEXT DEFAULT '',
                actionable_insight TEXT DEFAULT '',
                ai_quality_score REAL DEFAULT 0
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
        self._migrate_sqlite()

    def _init_tables_postgres(self):
        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content_items (
                id SERIAL PRIMARY KEY,
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
                tags TEXT,
                core_conclusion TEXT DEFAULT '',
                actionable_insight TEXT DEFAULT '',
                ai_quality_score REAL DEFAULT 0
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS creators (
                id SERIAL PRIMARY KEY,
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
                id SERIAL PRIMARY KEY,
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
                id SERIAL PRIMARY KEY,
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
                id SERIAL PRIMARY KEY,
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
                id SERIAL PRIMARY KEY,
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
                id SERIAL PRIMARY KEY,
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
                id SERIAL PRIMARY KEY,
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

    def _migrate_sqlite(self):
        """Add columns that may not exist in older SQLite databases."""
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
            if self.use_postgres:
                self._execute("""
                    INSERT INTO content_items
                    (module, content_type, title, url, source, platform, category,
                     summary, content, transcript, relevance_score, creator_name,
                     duration_seconds, published_at, fetched_at, tags)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (url) DO NOTHING
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
                return True
            else:
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
        except Exception:
            return False

    def save_article(self, article: dict) -> bool:
        article.setdefault("module", "geo")
        article.setdefault("content_type", "article")
        article.setdefault("platform", "rss")
        return self.save_content_item(article)

    def get_unused_content(self, module: str = "geo", limit: int = 15,
                           min_score: float = 0.3) -> list:
        ph = self._ph(3)
        cursor = self._execute(f"""
            SELECT * FROM content_items
            WHERE module = {self._ph()} AND used_in_briefing = 0
                  AND relevance_score >= {self._ph()}
            ORDER BY relevance_score DESC, published_at DESC
            LIMIT {self._ph()}
        """, (module, min_score, limit))
        return self._fetchall_as_dicts(cursor)

    def get_unused_articles(self, limit: int = 15,
                            min_score: float = 0.3) -> list:
        return self.get_unused_content("geo", limit, min_score)

    def update_enrichment(self, item_id: int, core_conclusion: str,
                          actionable_insight: str, ai_quality_score: float):
        if self.use_postgres:
            self._execute("""
                UPDATE content_items
                SET core_conclusion = %s, actionable_insight = %s,
                    ai_quality_score = %s
                WHERE id = %s
            """, (core_conclusion, actionable_insight, ai_quality_score, item_id))
        else:
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
            cursor = self._execute(f"""
                SELECT * FROM content_items
                WHERE ai_quality_score = 0 AND module = {self._ph()}
                ORDER BY relevance_score DESC LIMIT {self._ph()}
            """, (module, limit))
        else:
            cursor = self._execute(f"""
                SELECT * FROM content_items
                WHERE ai_quality_score = 0
                ORDER BY relevance_score DESC LIMIT {self._ph()}
            """, (limit,))
        return self._fetchall_as_dicts(cursor)

    def mark_content_used(self, item_ids: list):
        if not item_ids:
            return
        if self.use_postgres:
            placeholders = ",".join(["%s" for _ in item_ids])
        else:
            placeholders = ",".join(["?" for _ in item_ids])
        self._execute(
            f"UPDATE content_items SET used_in_briefing = 1 "
            f"WHERE id IN ({placeholders})",
            tuple(item_ids)
        )
        self.conn.commit()

    def mark_articles_used(self, article_ids: list):
        self.mark_content_used(article_ids)

    def get_content_by_date_range(self, start_date: str, end_date: str,
                                  module: str = None) -> list:
        if module:
            cursor = self._execute(f"""
                SELECT * FROM content_items
                WHERE fetched_at >= {self._ph()} AND fetched_at <= {self._ph()} AND module = {self._ph()}
                ORDER BY relevance_score DESC
            """, (start_date, end_date, module))
        else:
            cursor = self._execute(f"""
                SELECT * FROM content_items
                WHERE fetched_at >= {self._ph()} AND fetched_at <= {self._ph()}
                ORDER BY relevance_score DESC
            """, (start_date, end_date))
        return self._fetchall_as_dicts(cursor)

    def get_articles_by_date_range(self, start_date: str,
                                   end_date: str) -> list:
        return self.get_content_by_date_range(start_date, end_date, "geo")

    def get_content_by_module(self, module: str, limit: int = 50) -> list:
        cursor = self._execute(f"""
            SELECT * FROM content_items WHERE module = {self._ph()}
            ORDER BY fetched_at DESC LIMIT {self._ph()}
        """, (module, limit))
        return self._fetchall_as_dicts(cursor)

    # === 创作者管理 ===

    def save_creator(self, creator: dict) -> int:
        if self.use_postgres:
            cursor = self._execute("""
                INSERT INTO creators
                (name, platform, channel_url, rss_url, focus_area, notes, added_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
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
            row = cursor.fetchone()
            return row["id"] if row else 0
        else:
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
            cursor = self._execute(f"""
                SELECT * FROM creators WHERE platform = {self._ph()} AND active = 1
            """, (platform,))
        else:
            cursor = self._execute(
                "SELECT * FROM creators WHERE active = 1", ()
            )
        return self._fetchall_as_dicts(cursor)

    # === 简报操作 ===

    def save_briefing(self, date_str: str, content: str, article_count: int,
                      month_theme: str = "", module: str = "geo"):
        if self.use_postgres:
            self._execute("""
                INSERT INTO briefings
                (module, date, content, article_count, month_theme, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (module, date) DO UPDATE SET
                    content = EXCLUDED.content,
                    article_count = EXCLUDED.article_count,
                    month_theme = EXCLUDED.month_theme,
                    created_at = EXCLUDED.created_at
            """, (module, date_str, content, article_count, month_theme,
                  datetime.now().isoformat()))
        else:
            self.conn.execute("""
                INSERT OR REPLACE INTO briefings
                (module, date, content, article_count, month_theme, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (module, date_str, content, article_count, month_theme,
                  datetime.now().isoformat()))
        self.conn.commit()

    def get_briefing(self, date_str: str,
                     module: str = "geo") -> Optional[dict]:
        cursor = self._execute(f"""
            SELECT * FROM briefings WHERE date = {self._ph()} AND module = {self._ph()}
        """, (date_str, module))
        return self._fetchone_as_dict(cursor)

    def get_briefings_by_range(self, start_date: str, end_date: str,
                               module: str = None) -> list:
        if module:
            cursor = self._execute(f"""
                SELECT * FROM briefings
                WHERE date >= {self._ph()} AND date <= {self._ph()} AND module = {self._ph()}
                ORDER BY date
            """, (start_date, end_date, module))
        else:
            cursor = self._execute(f"""
                SELECT * FROM briefings
                WHERE date >= {self._ph()} AND date <= {self._ph()}
                ORDER BY date
            """, (start_date, end_date))
        return self._fetchall_as_dicts(cursor)

    # === 测验操作 ===

    def save_quiz(self, date_str: str, questions: str,
                  module: str = "geo") -> int:
        if self.use_postgres:
            cursor = self._execute("""
                INSERT INTO quizzes (module, date, questions, created_at)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (module, date_str, questions, datetime.now().isoformat()))
            self.conn.commit()
            row = cursor.fetchone()
            return row["id"] if row else 0
        else:
            cursor = self.conn.execute("""
                INSERT INTO quizzes (module, date, questions, created_at)
                VALUES (?, ?, ?, ?)
            """, (module, date_str, questions, datetime.now().isoformat()))
            self.conn.commit()
            return cursor.lastrowid

    def save_quiz_result(self, quiz_id: int, answers: str, score: float):
        if self.use_postgres:
            self._execute("""
                UPDATE quizzes SET answers = %s, score = %s, completed = 1
                WHERE id = %s
            """, (answers, score, quiz_id))
        else:
            self.conn.execute("""
                UPDATE quizzes SET answers = ?, score = ?, completed = 1
                WHERE id = ?
            """, (answers, score, quiz_id))
        self.conn.commit()

    def get_quiz(self, date_str: str,
                 module: str = "geo") -> Optional[dict]:
        cursor = self._execute(f"""
            SELECT * FROM quizzes WHERE date = {self._ph()} AND module = {self._ph()}
            ORDER BY id DESC LIMIT 1
        """, (date_str, module))
        return self._fetchone_as_dict(cursor)

    def get_quiz_scores(self, start_date: str, end_date: str,
                        module: str = None) -> list:
        if module:
            cursor = self._execute(f"""
                SELECT date, score, module FROM quizzes
                WHERE date >= {self._ph()} AND date <= {self._ph()} AND completed = 1
                      AND module = {self._ph()}
                ORDER BY date
            """, (start_date, end_date, module))
        else:
            cursor = self._execute(f"""
                SELECT date, score, module FROM quizzes
                WHERE date >= {self._ph()} AND date <= {self._ph()} AND completed = 1
                ORDER BY date
            """, (start_date, end_date))
        return self._fetchall_as_dicts(cursor)

    # === 学习记录 ===

    def log_activity(self, activity_type: str, duration_minutes: int = 0,
                     notes: str = "", module: str = "geo"):
        if self.use_postgres:
            self._execute("""
                INSERT INTO learning_log
                (module, date, activity_type, duration_minutes, notes, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (module, date.today().isoformat(), activity_type,
                  duration_minutes, notes, datetime.now().isoformat()))
        else:
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
            cursor = self._execute(f"""
                SELECT
                    COUNT(DISTINCT date) as active_days,
                    SUM(duration_minutes) as total_minutes,
                    COUNT(*) as total_activities
                FROM learning_log
                WHERE date >= {self._ph()} AND date <= {self._ph()} AND module = {self._ph()}
            """, (start_date, end_date, module))
        else:
            cursor = self._execute(f"""
                SELECT
                    COUNT(DISTINCT date) as active_days,
                    SUM(duration_minutes) as total_minutes,
                    COUNT(*) as total_activities
                FROM learning_log
                WHERE date >= {self._ph()} AND date <= {self._ph()}
            """, (start_date, end_date))
        result = self._fetchone_as_dict(cursor)
        return result if result else {}

    # === 周报/月报 ===

    def save_weekly_report(self, week_number: int, year: int,
                           start_date: str, end_date: str,
                           content: str, key_insights: str = "",
                           module: str = "all"):
        if self.use_postgres:
            self._execute("""
                INSERT INTO weekly_reports
                (module, week_number, year, start_date, end_date, content,
                 key_insights, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (module, week_number, year) DO UPDATE SET
                    start_date = EXCLUDED.start_date,
                    end_date = EXCLUDED.end_date,
                    content = EXCLUDED.content,
                    key_insights = EXCLUDED.key_insights,
                    created_at = EXCLUDED.created_at
            """, (module, week_number, year, start_date, end_date, content,
                  key_insights, datetime.now().isoformat()))
        else:
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
        if self.use_postgres:
            self._execute("""
                INSERT INTO monthly_reports
                (module, month, year, content, month_theme, key_learnings,
                 created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (module, month, year) DO UPDATE SET
                    content = EXCLUDED.content,
                    month_theme = EXCLUDED.month_theme,
                    key_learnings = EXCLUDED.key_learnings,
                    created_at = EXCLUDED.created_at
            """, (module, month, year, content, month_theme, key_learnings,
                  datetime.now().isoformat()))
        else:
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
        if self.use_postgres:
            self._execute("""
                INSERT INTO knowledge_base
                (module, topic, category, content, source_articles, tags,
                 cross_modules, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (module, topic, category, content, source_articles, tags,
                  cross_modules, now, now))
        else:
            self.conn.execute("""
                INSERT INTO knowledge_base
                (module, topic, category, content, source_articles, tags,
                 cross_modules, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (module, topic, category, content, source_articles, tags,
                  cross_modules, now, now))
        self.conn.commit()

    def search_knowledge(self, keyword: str, module: str = None) -> list:
        like_pattern = f"%{keyword}%"
        if module:
            cursor = self._execute(f"""
                SELECT * FROM knowledge_base
                WHERE (topic LIKE {self._ph()} OR content LIKE {self._ph()} OR tags LIKE {self._ph()}
                       OR cross_modules LIKE {self._ph()})
                      AND module = {self._ph()}
                ORDER BY updated_at DESC
            """, (like_pattern, like_pattern, like_pattern, like_pattern, module))
        else:
            cursor = self._execute(f"""
                SELECT * FROM knowledge_base
                WHERE topic LIKE {self._ph()} OR content LIKE {self._ph()} OR tags LIKE {self._ph()}
                      OR cross_modules LIKE {self._ph()}
                ORDER BY updated_at DESC
            """, (like_pattern, like_pattern, like_pattern, like_pattern))
        return self._fetchall_as_dicts(cursor)

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
