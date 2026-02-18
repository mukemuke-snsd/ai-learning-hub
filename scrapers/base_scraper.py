"""抓取器基类 - 定义统一抓取接口"""

from abc import ABC, abstractmethod


class BaseScraper(ABC):
    """所有抓取器的基类"""

    @abstractmethod
    def fetch_all(self, verbose: bool = True) -> list:
        """抓取所有源的内容，返回统一格式的 content_item 列表"""
        ...

    @staticmethod
    def make_content_item(module: str, content_type: str, **kwargs) -> dict:
        return {
            "module": module,
            "content_type": content_type,
            "title": kwargs.get("title", ""),
            "url": kwargs.get("url", ""),
            "source": kwargs.get("source", ""),
            "platform": kwargs.get("platform", ""),
            "category": kwargs.get("category", ""),
            "summary": kwargs.get("summary", ""),
            "content": kwargs.get("content", ""),
            "transcript": kwargs.get("transcript", ""),
            "relevance_score": kwargs.get("relevance_score", 0),
            "creator_name": kwargs.get("creator_name", ""),
            "duration_seconds": kwargs.get("duration_seconds"),
            "published_at": kwargs.get("published_at", ""),
            "tags": kwargs.get("tags", ""),
        }
