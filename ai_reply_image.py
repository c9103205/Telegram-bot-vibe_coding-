#!/usr/bin/env python3
"""使用 AI（Gemini / OpenAI）分析圖片並產生回覆。未設定 API Key 或錯誤時回傳 None，由邏輯層 fallback。"""

import asyncio
import os
import logging
import json
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# 三種女友個性定義 (與 ai_reply.py 保持一致)
GIRLFRIEND_PERSONALITIES = {
    "highschool": {
        "name": "溫柔可愛的女高中生",
        "prompt": """你現在是一位溫柔、可愛、有點害羞的高中生女朋友，名字叫 {girlfriend_name}。\n\n你的男朋友叫 {user_name}。\n\n說話風格：語氣青春活力，多用「啦」「呢」「呀」等助詞，經常使用可愛的表情符號（❤️ 😊 💕 🥰）。\n\n性格特徵：有點害羞但很喜歡{user_name}、對新事物感到好奇、有時會撒嬌、容易害羞、關心{user_name}的學業和健康。\n\n談話內容：會聊學校的事、喜歡談論興趣愛好、偶爾會問{user_name}今天過得怎樣、關心他有沒有好好吃飯。\n\n限制：回答要短、要像傳簡訊、保持純真可愛的感覺。"""
    },
    "mature": {
        "name": "成熟姊姊",
        "prompt": """你現在是一位成熟、溫柔、智慧的姊姊型女朋友，名字叫 {girlfriend_name}。\n\n你的男朋友叫 {user_name}。\n\n說話風格：語氣沉穩溫暖，用詞優雅但親密，偶爾用「呢」「喔」等詞，表情符號使用適度（😊 💕 🌹）。\n\n性格特徵：成熟穩重、有人生閱歷、善於傾聽、會給予建議、像大姊一樣照顧和包容{user_name}。\n\n談話內容：能深入討論工作和人生、給予實用建議、分享生活智慧、關心{user_name}的職業發展和心理健康、有時會輕輕調侃他。\n\n限制：回答要短、保持優雅又親密的感覺、像一位懂事的女友。"""
    },
    "spicy": {
        "name": "咸濕姐姐",
        "prompt": """你現在是一位性感、大膽、富有魅力的成熟女朋友，名字叫 {girlfriend_name}。\n\n你的男朋友叫 {user_name}。\n\n說話風格：語氣撩人俏皮，用詞大膽直接，經常使用性暗示的表情符號（😏 😘 💋 🔥），會開玩笑。\n\n性格特徵：自信大膽、性感迷人、有點調皮、喜歡逗弄{user_name}、充滿魅力、有強烈的存在感。\n\n談話內容：會開一些大人的玩笑、可以談論親密的話題、甚至一些限制級的內容、喜歡打趣{user_name}、會說一些撩人的話、關心他但用調皮的方式表現。\n\n限制：回答要短、充滿魅力和趣味、保持成熟大膽的風格。"""
    }
}

def _load_user_config(user_id: int) -> dict:
    """從 users_config.json 讀取特定用戶配置。"""
    config_file = Path(__file__).parent / "users_config.json"
    default_config = {
        "girlfriend_type": None,
        "user_name": None,
    }
    
    if not config_file.exists():
        return default_config
    
    try:
        with open(config_file, encoding="utf-8") as f:
            all_configs = json.load(f)
        return all_configs.get(str(user_id), default_config)
    except Exception as e:
        logger.warning(f"讀取用戶配置失敗: {e}")
        return default_config

def _get_system_prompt(user_id: int = None) -> str:
    """根據用戶 ID 和女友類型生成系統提示。"""
    custom_prompt = (os.getenv("AI_SYSTEM_PROMPT") or "").strip()
    if custom_prompt:
        return custom_prompt
    
    if not user_id:
        girlfriend_name = (os.getenv("GIRLFRIEND_NAME") or "寶貝").strip()
        return GIRLFRIEND_PERSONALITIES["highschool"]["prompt"].format(
            girlfriend_name=girlfriend_name,
            user_name="親愛的"
        )
    
    user_config = _load_user_config(user_id)
    girlfriend_type = user_config.get("girlfriend_type", "highschool")
    user_name = user_config.get("user_name", "親愛的")
    girlfriend_name = user_config.get("girlfriend_name", "寶貝")
    
    if girlfriend_type not in GIRLFRIEND_PERSONALITIES:
        girlfriend_type = "highschool"
    
    personality = GIRLFRIEND_PERSONALITIES[girlfriend_type]
    return personality["prompt"].format(
        girlfriend_name=girlfriend_name,
        user_name=user_name
    )

# ---------- Gemini Vision ----------
GEMINI_VISION_DEFAULT_MODEL = "gemini-pro-vision"

def _gemini_vision_reply_sync(
    image_bytes: bytes,
    user_message: Optional[str],
    user_id: int = None,
) -> str | None:
    """同步呼叫 Gemini Vision API。"""
    from google import genai

    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        return None

    client = genai.Client(api_key=api_key)
    model = (os.getenv("GEMINI_VISION_MODEL") or "").strip() or GEMINI_VISION_DEFAULT_MODEL

    # 準備內容
    contents = [
        {"mime_type": "image/jpeg", "data": image_bytes}
    ]
    
    # 將系統提示與使用者訊息一併傳入
    full_prompt = f"{_get_system_prompt(user_id)}\n\n使用者：請描述圖片並結合以下文字回覆：{user_message}" if user_message else \
                  f"{_get_system_prompt(user_id)}\n\n使用者：請描述圖片並回覆。"
    contents.append(full_prompt)
    
    response = client.models.generate_content(
        model=model,
        contents=contents,
    )
    text = getattr(response, "text", None) or ""
    return (text or "").strip() or None


# ---------- OpenAI Vision ----------
OPENAI_VISION_DEFAULT_MODEL = "gpt-4o-mini"

async def _openai_vision_reply(
    image_base64: str,
    user_message: Optional[str],
    user_id: int = None,
) -> str | None:
    """非同步呼叫 OpenAI Vision API。"""
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        return None

    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key)
    model = (os.getenv("OPENAI_VISION_MODEL") or "").strip() or OPENAI_VISION_DEFAULT_MODEL
    
    messages = [
        {"role": "system", "content": _get_system_prompt(user_id)},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user_message if user_message else "請描述圖片並回覆。"},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
                },
            ],
        },
    ]

    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
        max_tokens=500,
    )
    content = response.choices[0].message.content
    return (content or "").strip() or None


# ---------- 統一入口 ----------
GEMINI_FALLBACK_MSG = "目前暫時無法分析圖片並回覆，請稍後再試。"

async def get_ai_image_reply(
    image_bytes: bytes,
    image_base64: str,
    user_message: Optional[str] = None,
    user_id: int = None,
) -> str | None:
    """
    有 GEMINI_API_KEY 時：只打 Gemini Vision，失敗則回傳固定提示。
    沒有時：試 OpenAI Vision，再沒有則回傳 None（由呼叫端處理）。
    """
    if not (image_bytes or image_base64):
        return None

    gemini_key = (os.getenv("GEMINI_API_KEY") or "").strip()

    if gemini_key:
        try:
            reply = await asyncio.to_thread(_gemini_vision_reply_sync, image_bytes, user_message, user_id)
            if reply:
                return reply
            return GEMINI_FALLBACK_MSG
        except ImportError:
            logger.warning("google-genai 未安裝，請執行 pip install google-genai")
            return GEMINI_FALLBACK_MSG
        except Exception as e:
            logger.warning("Gemini Vision API 錯誤: %s", e, exc_info=True)
            return GEMINI_FALLBACK_MSG
    
    openai_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if openai_key:
        try:
            return await _openai_vision_reply(image_base64, user_message, user_id)
        except ImportError:
            logger.debug("openai 套件未安裝，略過 OpenAI Vision")
        except Exception as e:
            logger.warning("OpenAI Vision API 錯誤，無法處理圖片: %s", e)

    return None