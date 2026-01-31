#!/usr/bin/env python3
"""使用 AI（Gemini / OpenAI）產生回覆。未設定 API Key 或錯誤時回傳 None，由邏輯層 fallback。"""

import asyncio
import os
import logging

logger = logging.getLogger(__name__)

# 系統提示（可透過環境變數 AI_SYSTEM_PROMPT 覆蓋）
DEFAULT_SYSTEM_PROMPT = (
    "你是 Telegram 上的友善助理。請用簡短、自然的語氣回覆使用者，"
    "每則回覆控制在 1～3 句話內，除非使用者明確要求長文。"
)


def _get_system_prompt() -> str:
    return (os.getenv("AI_SYSTEM_PROMPT") or "").strip() or DEFAULT_SYSTEM_PROMPT


# ---------- Gemini ----------
# 此 API 版本不支援 gemini-1.5-flash（會 404），請用 gemini-2.0-flash
GEMINI_DEFAULT_MODEL = "gemini-2.0-flash"


def _gemini_reply_sync(user_message: str) -> str | None:
    """同步呼叫 Gemini API（會在 async 裡用 to_thread 執行）。"""
    from google import genai

    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        return None

    client = genai.Client(api_key=api_key)
    model = (os.getenv("GEMINI_MODEL") or "").strip() or GEMINI_DEFAULT_MODEL
    # 將系統提示與使用者訊息一併傳入（Gemini generate_content 可用 contents 多段）
    full_prompt = f"{_get_system_prompt()}\n\n使用者：{user_message}"
    response = client.models.generate_content(
        model=model,
        contents=full_prompt,
    )
    text = getattr(response, "text", None) or ""
    return (text or "").strip() or None


# ---------- OpenAI ----------
OPENAI_DEFAULT_MODEL = "gpt-4o-mini"


async def _openai_reply(user_message: str) -> str | None:
    """非同步呼叫 OpenAI Chat Completions。"""
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        return None

    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key)
    model = (os.getenv("OPENAI_MODEL") or "").strip() or OPENAI_DEFAULT_MODEL
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _get_system_prompt()},
            {"role": "user", "content": user_message},
        ],
        temperature=0.7,
        max_tokens=500,
    )
    content = response.choices[0].message.content
    return (content or "").strip() or None


# ---------- 統一入口 ----------

# 有設 GEMINI_API_KEY 但 API 失敗時的回覆（不再用關鍵字）
GEMINI_FALLBACK_MSG = "目前暫時無法回覆，請稍後再試。"


async def get_ai_reply(user_message: str) -> str | None:
    """
    有 GEMINI_API_KEY 時：只打 Gemini，失敗則回傳固定提示。
    沒有時：試 OpenAI，再沒有則回傳 None（由呼叫端用關鍵字回覆）。
    """
    if not (user_message or (user_message and user_message.strip())):
        return None

    gemini_key = (os.getenv("GEMINI_API_KEY") or "").strip()

    # 有設 Gemini → 直接打 Gemini，不試 OpenAI、不退回關鍵字
    if gemini_key:
        try:
            reply = await asyncio.to_thread(_gemini_reply_sync, user_message.strip())
            if reply:
                return reply
            return GEMINI_FALLBACK_MSG
        except ImportError:
            logger.warning("google-genai 未安裝，請執行 pip install google-genai")
            return GEMINI_FALLBACK_MSG
        except Exception as e:
            logger.warning("Gemini API 錯誤: %s", e, exc_info=True)
            return GEMINI_FALLBACK_MSG

    # 未設 Gemini：試 OpenAI
    openai_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if openai_key:
        try:
            return await _openai_reply(user_message)
        except ImportError:
            logger.debug("openai 套件未安裝，略過 OpenAI")
        except Exception as e:
            logger.warning("OpenAI API 錯誤，改用關鍵字回覆: %s", e)

    return None
