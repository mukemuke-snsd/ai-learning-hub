"""配置加载器 - 支持多模块的配置管理"""

import os
import yaml
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")


def get_project_root() -> Path:
    return Path(__file__).parent.parent


def load_yaml(filepath: str) -> dict:
    """加载 YAML 文件（支持绝对路径或相对于 config/ 的路径）"""
    path = Path(filepath)
    if not path.is_absolute():
        path = get_project_root() / "config" / filepath
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_settings() -> dict:
    settings = load_yaml("settings.yaml")
    api_key = os.environ.get("OPENAI_API_KEY", "")
    settings["openai"]["api_key"] = api_key
    return settings


def load_module_config(module_id: str) -> dict:
    """加载指定模块的配置"""
    return load_yaml(f"modules/{module_id}.yaml")


def load_all_module_configs() -> dict:
    """加载所有已启用模块的配置"""
    settings = load_settings()
    enabled = settings.get("modules", ["product_radar", "research_lab"])
    configs = {}
    for mid in enabled:
        try:
            configs[mid] = load_module_config(mid)
        except FileNotFoundError:
            pass
    return configs


def get_module_learning_track(module_id: str) -> dict:
    cfg = load_module_config(module_id)
    return cfg.get("learning_track", {})


def get_module_keywords(module_id: str) -> dict:
    cfg = load_module_config(module_id)
    return cfg.get("keywords", {})


# 兼容旧接口：load_sources 返回 product_radar 模块配置
def load_sources() -> dict:
    return load_module_config("product_radar")


def get_data_path(subdir: str = "") -> Path:
    base = get_project_root() / "data"
    if subdir:
        path = base / subdir
    else:
        path = base
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_db_path() -> Path:
    """获取 SQLite 数据库路径（本地开发用）"""
    env_path = os.environ.get("AI_LEARNING_HUB_DB_PATH")
    if env_path:
        return Path(env_path)
    settings = load_settings()
    return get_project_root() / settings["paths"]["database"]


def get_database_url() -> Optional[str]:
    """获取数据库连接 URL。优先读 DATABASE_URL 环境变量（Supabase），否则返回 None（本地用 SQLite）"""
    return os.environ.get("DATABASE_URL")
