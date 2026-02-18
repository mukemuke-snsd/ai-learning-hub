"""转录处理器 - 字幕清洗、分段、格式化"""

import re
from typing import Optional

from config.loader import load_settings

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


class TranscriptProcessor:
    """视频/音频转录文本处理"""

    def __init__(self):
        self.settings = load_settings()

    def clean_transcript(self, raw_text: str) -> str:
        """清洗原始字幕文本"""
        if not raw_text:
            return ""

        text = raw_text
        # 去除时间戳 [00:01:23]
        text = re.sub(r'\[?\d{1,2}:\d{2}(?::\d{2})?\]?', '', text)
        # 去除 HTML 标签
        text = re.sub(r'<[^>]+>', '', text)
        # 去除连续空格
        text = re.sub(r'\s+', ' ', text)
        # 去除重复片段（字幕常见问题）
        lines = text.split('.')
        seen = set()
        unique = []
        for line in lines:
            stripped = line.strip().lower()
            if stripped and stripped not in seen:
                seen.add(stripped)
                unique.append(line.strip())
        text = '. '.join(unique)

        return text.strip()

    def segment_text(self, text: str, max_chars: int = 3000) -> list:
        """将长文本分段，每段不超过 max_chars 字符"""
        if len(text) <= max_chars:
            return [text]

        segments = []
        sentences = re.split(r'(?<=[.!?。！？])\s+', text)
        current = ""

        for sentence in sentences:
            if len(current) + len(sentence) + 1 > max_chars:
                if current:
                    segments.append(current.strip())
                current = sentence
            else:
                current = f"{current} {sentence}" if current else sentence

        if current:
            segments.append(current.strip())

        return segments

    def summarize_transcript(self, transcript: str,
                             title: str = "",
                             creator: str = "") -> str:
        """用 AI 生成转录文本的结构化摘要"""
        if not HAS_OPENAI or not transcript:
            return ""

        ai_config = self.settings.get("openai", {})
        if not ai_config.get("api_key"):
            return ""

        client = OpenAI(api_key=ai_config["api_key"])
        preview = transcript[:4000]

        system_prompt = (
            "你是一位产品经理学习教练。"
            "请将视频/播客的转录文本提炼为简洁的中文摘要。\n"
            "输出结构：\n"
            "1. 一句话概要\n"
            "2. 3-5个核心观点\n"
            "3. 1-2个产品经理可借鉴的行动点"
        )

        user_prompt = (
            f"标题: {title}\n博主: {creator}\n\n"
            f"转录内容:\n{preview}"
        )

        try:
            response = client.chat.completions.create(
                model=ai_config.get("model", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.5,
                max_tokens=1000,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return ""

    def transcribe_audio_whisper(self, audio_path: str) -> str:
        """使用 OpenAI Whisper API 转录音频文件（备选方案）"""
        if not HAS_OPENAI:
            return ""

        ai_config = self.settings.get("openai", {})
        if not ai_config.get("api_key"):
            return ""

        client = OpenAI(api_key=ai_config["api_key"])

        try:
            with open(audio_path, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text",
                )
            return transcription
        except Exception:
            return ""
