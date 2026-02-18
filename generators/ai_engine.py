"""AI 引擎 - 封装 OpenAI API 调用"""

import json
from typing import Optional

from openai import OpenAI

from config.loader import load_settings


class AIEngine:
    """OpenAI API 封装"""

    def __init__(self):
        settings = load_settings()
        ai_config = settings.get("openai", {})
        self.client = OpenAI(
            api_key=ai_config.get("api_key", ""),
            base_url=ai_config.get("base_url", "https://api.openai.com/v1"),
        )
        self.model = ai_config.get("model", "gpt-4o-mini")
        self.model_advanced = ai_config.get("model_advanced", "gpt-4o")
        self.temperature = ai_config.get("temperature", 0.7)
        self.max_tokens = ai_config.get("max_tokens", 4000)

    def generate(self, system_prompt: str, user_prompt: str,
                 use_advanced: bool = False,
                 max_tokens: Optional[int] = None,
                 temperature: Optional[float] = None) -> str:
        model = self.model_advanced if use_advanced else self.model
        tokens = max_tokens or self.max_tokens
        temp = temperature if temperature is not None else self.temperature
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temp,
                max_tokens=tokens,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"[AI 生成失败: {str(e)}]"

    def generate_json(self, system_prompt: str, user_prompt: str,
                      use_advanced: bool = False) -> dict:
        model = self.model_advanced if use_advanced else self.model
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content.strip()
            return json.loads(content)
        except json.JSONDecodeError:
            return {"error": "JSON 解析失败", "raw": content}
        except Exception as e:
            return {"error": str(e)}
