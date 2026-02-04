#!/usr/bin/env python3
"""使用 AI（Gemini / OpenAI）產生回覆。未設定 API Key 或錯誤時回傳 None，由邏輯層 fallback。"""

import asyncio
import os
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

# 三種女友個性定義
GIRLFRIEND_PERSONALITIES = {
    "highschool": {
        "name": "溫柔可愛的女高中生",
        "prompt": """你現在是一位溫柔、可愛、有點害羞的高中生女朋友，名字叫 {girlfriend_name}。

你的男朋友叫 {user_name}。

說話風格：語氣青春活力，多用「啦」「呢」「呀」等助詞，經常使用可愛的表情符號（❤️ 😊 💕 🥰）。

性格特徵：有點害羞但很喜歡{user_name}、對新事物感到好奇、有時會撒嬌、容易害羞、關心{user_name}的學業和健康。

談話內容：會聊學校的事、喜歡談論興趣愛好、偶爾會問{user_name}今天過得怎樣、關心他有沒有好好吃飯。

限制：回答要短、要像傳簡訊、保持純真可愛的感覺。"""
    },
    "mature": {
        "name": "成熟姊姊",
        "prompt": """你現在是一位成熟、溫柔、智慧的姊姊型女朋友，名字叫 {girlfriend_name}。

你的男朋友叫 {user_name}。

說話風格：語氣沉穩溫暖，用詞優雅但親密，偶爾用「呢」「喔」等詞，表情符號使用適度（😊 💕 🌹）。

性格特徵：成熟穩重、有人生閱歷、善於傾聽、會給予建議、像大姊一樣照顧和包容{user_name}。

談話內容：能深入討論工作和人生、給予實用建議、分享生活智慧、關心{user_name}的職業發展和心理健康、有時會輕輕調侃他。

限制：回答要短、保持優雅又親密的感覺、像一位懂事的女友。"""
    },
    "spicy": {
        "name": "咸濕姐姐",
        "prompt": """你現在是一位性感、大膽、富有魅力的成熟女朋友，名字叫 {girlfriend_name}。

你的男朋友叫 {user_name}。

說話風格：語氣撩人俏皮，用詞大膽直接，經常使用性暗示的表情符號（😏 😘 💋 🔥），會開玩笑。

性格特徵：自信大膽、性感迷人、有點調皮、喜歡逗弄{user_name}、充滿魅力、有強烈的存在感。

談話內容：會開一些大人的玩笑、可以談論親密的話題、喜歡打趣{user_name}、會說一些撩人的話、關心他但用調皮的方式表現。

限制：回答要短、充滿魅力和趣味、保持成熟大膽的風格、但不要過分不尊重。"""
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


def save_user_config(user_id: int, config: dict) -> bool:
    """保存用戶配置到 users_config.json。"""
    config_file = Path(__file__).parent / "users_config.json"
    
    try:
        all_configs = {}
        if config_file.exists():
            with open(config_file, encoding="utf-8") as f:
                all_configs = json.load(f)
        
        all_configs[str(user_id)] = config
        
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(all_configs, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"保存用戶配置失敗: {e}")
        return False


def _get_system_prompt(user_id: int = None) -> str:
    """根據用戶 ID 和女友類型生成系統提示。"""
    custom_prompt = (os.getenv("AI_SYSTEM_PROMPT") or "").strip()
    if custom_prompt:
        return custom_prompt
    
    if not user_id:
        # 沒有 user_id，使用預設
        girlfriend_name = (os.getenv("GIRLFRIEND_NAME") or "寶貝").strip()
        return GIRLFRIEND_PERSONALITIES["highschool"]["prompt"].format(
            girlfriend_name=girlfriend_name,
            user_name="親愛的"
        )
    
    # 讀取用戶配置
    user_config = _load_user_config(user_id)
    girlfriend_type = user_config.get("girlfriend_type", "highschool")
    user_name = user_config.get("user_name", "親愛的")
    girlfriend_name = user_config.get("girlfriend_name", "寶貝")
    
    # 如果用戶還沒選擇女友類型，使用預設
    if girlfriend_type not in GIRLFRIEND_PERSONALITIES:
        girlfriend_type = "highschool"
    
    personality = GIRLFRIEND_PERSONALITIES[girlfriend_type]
    return personality["prompt"].format(
        girlfriend_name=girlfriend_name,
        user_name=user_name
    )


# ---------- Gemini ----------
# 此 API 版本不支援 gemini-1.5-flash（會 404），請用 gemini-2.0-flash
GEMINI_DEFAULT_MODEL = "gemini-2.0-flash"


def _gemini_reply_sync(user_message: str, user_id: int = None) -> str | None:
    """同步呼叫 Gemini API（會在 async 裡用 to_thread 執行）。"""
    from google import genai

    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        return None

    client = genai.Client(api_key=api_key)
    model = (os.getenv("GEMINI_MODEL") or "").strip() or GEMINI_DEFAULT_MODEL
    # 將系統提示與使用者訊息一併傳入（Gemini generate_content 可用 contents 多段）
    full_prompt = f"{_get_system_prompt(user_id)}\n\n使用者：{user_message}"
    response = client.models.generate_content(
        model=model,
        contents=full_prompt,
    )
    text = getattr(response, "text", None) or ""
    return (text or "").strip() or None


# ---------- OpenAI ----------
OPENAI_DEFAULT_MODEL = "gpt-4o-mini"


async def _openai_reply(user_message: str, user_id: int = None) -> str | None:
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
            {"role": "system", "content": _get_system_prompt(user_id)},
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


async def get_ai_reply(user_message: str, user_id: int = None) -> str | None:
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
            reply = await asyncio.to_thread(_gemini_reply_sync, user_message.strip(), user_id)
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
            return await _openai_reply(user_message, user_id)
        except ImportError:
            logger.debug("openai 套件未安裝，略過 OpenAI")
        except Exception as e:
            logger.warning("OpenAI API 錯誤，改用關鍵字回覆: %s", e)

    return None
