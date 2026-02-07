#!/usr/bin/env python3
"""使用 AI（Gemini / OpenAI）生成圖片。"""

import asyncio
import os
import logging
from io import BytesIO
import json
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# 生成圖片時的人物一致性與風格（每張圖都套用）
IMAGE_CHARACTER_TRAITS = (
    "自拍感強烈，像真人自拍照片，"
    "人物一致：台灣年輕女性，黑色長直髮，"
    "構圖與光線像手機自拍、臉部特寫或半身。"
)

# 三種女友個性定義 (與 ai_reply.py 保持一致)，已含自拍感與人物設定
GIRLFRIEND_PERSONALITIES = {
    "highschool": {
        "name": "溫柔可愛的女高中生",
        "prompt_prefix": (
            f"{IMAGE_CHARACTER_TRAITS} "
            "一個台灣年輕女性，黑色長直髮，穿著高中制服，非常可愛，第一人稱自拍角度，臉部特寫"
        ),
    },
    "mature": {
        "name": "成熟姊姊",
        "prompt_prefix": (
            f"{IMAGE_CHARACTER_TRAITS} "
            "一個台灣年輕女性，黑色長直髮，成熟性感，第一人稱自拍角度，臉部特寫"
        ),
    },
    "spicy": {
        "name": "咸濕姐姐",
        "prompt_prefix": (
            f"{IMAGE_CHARACTER_TRAITS} "
            "一個台灣年輕女性，黑色長直髮，性感大膽，穿著清涼，第一人稱自拍角度，臉部特寫"
        ),
    },
}

# 約 100 個關鍵字：使用者訊息包含任一個即觸發拍照（生成圖片）
IMAGE_TRIGGER_KEYWORDS = frozenset({
    "吃飯", "吃早餐", "吃午餐", "吃晚餐", "吃宵夜", "煮飯", "做菜", "喝咖啡", "喝茶", "喝飲料",
    "睡覺", "起床", "早安", "晚安", "午安", "賴床", "夢到你",
    "逛街", "購物", "買東西", "看電影", "電影", "唱歌", "跳舞", "聽音樂", "運動", "跑步", "健身", "游泳", "打球",
    "洗澡", "泡澡", "自拍", "拍照", "拍我", "想看你", "看看你", "給我看",
    "散步", "旅行", "出去玩", "約會", "見面", "等你",
    "上班", "下班", "上課", "下課", "讀書", "寫作業", "加班", "開會",
    "下雨", "晴天", "天氣", "好冷", "好熱", "今天",
    "心情好", "心情不好", "開心", "難過", "想你", "想你了", "抱抱", "親親", "愛你", "喜歡你",
    "生日", "節日", "聖誕節", "情人節", "過年", "放假", "週末",
    "早餐", "午餐", "晚餐", "宵夜", "點心", "甜點", "蛋糕", "冰淇淋",
    "咖啡廳", "餐廳", "家裡", "房間", "客廳", "廚房", "陽台",
    "貓", "狗", "寵物", "狗狗", "貓咪",
    "化妝", "打扮", "換衣服", "出門", "回家",
    "看書", "追劇", "打遊戲", "玩遊戲", "滑手機",
    "早安呀", "晚安呀", "在幹嘛", "在做什麼", "想我嗎",
    "好無聊", "好累", "好餓", "好睏", "好渴",
    "謝謝", "辛苦了", "加油", "掰掰", "再見",
})

def get_trigger_keyword(message: str) -> str | None:
    """
    若訊息包含任一觸發關鍵字，回傳該關鍵字（用於觸發拍照）；否則回傳 None。
    先完全符合，再依關鍵字長度由長到短匹配「包含」。
    """
    if not message or not message.strip():
        return None
    text = message.strip()
    if text in IMAGE_TRIGGER_KEYWORDS:
        return text
    for keyword in sorted(IMAGE_TRIGGER_KEYWORDS, key=len, reverse=True):
        if keyword in text:
            return keyword
    return None


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

def _get_image_gen_prompt(user_id: int = None, keyword: str = "") -> str:
    """根據用戶 ID 和女友類型生成圖片生成提示。強調自拍感、台灣年輕女性、黑色長直髮、人物一致。"""
    base_no_user = (
        f"{IMAGE_CHARACTER_TRAITS} "
        "一個台灣年輕女性，黑色長直髮，第一人稱自拍角度，臉部特寫"
    )
    if not user_id:
        return base_no_user + (f"，情境或背景：{keyword}" if keyword else "")
    
    user_config = _load_user_config(user_id)
    girlfriend_type = user_config.get("girlfriend_type", "highschool")
    
    if girlfriend_type not in GIRLFRIEND_PERSONALITIES:
        girlfriend_type = "highschool"
    
    personality = GIRLFRIEND_PERSONALITIES[girlfriend_type]
    prompt_prefix = personality.get("prompt_prefix", base_no_user)
    
    if keyword:
        return f"{prompt_prefix}，情境或背景：{keyword}"
    return prompt_prefix

# ---------- Gemini Image Generation ----------
# 圖片生成需使用支援 image generation 的模型，並設定 response_modalities
GEMINI_IMAGE_DEFAULT_MODEL = "gemini-2.0-flash-exp-image-generation"  # 實驗性圖片生成

def _gemini_generate_image_sync(
    prompt: str,
) -> bytes | None:
    """同步呼叫 Gemini Image Generation API 生成圖片。"""
    from google import genai
    from google.genai import types

    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        return None

    client = genai.Client(api_key=api_key)
    model = (os.getenv("GEMINI_IMAGE_MODEL") or "").strip() or GEMINI_IMAGE_DEFAULT_MODEL

    try:
        # 圖片生成必須設定 response_modalities=["TEXT", "IMAGE"]（API 規定須含 TEXT）
        response = client.models.generate_content(
            model=model,
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
            ),
        )
        
        image_bytes = None
        parts = getattr(response, "parts", None) or []
        if not parts and getattr(response, "candidates", None):
            c0 = response.candidates[0]
            if getattr(c0, "content", None) and getattr(c0.content, "parts", None):
                parts = c0.content.parts
        
        for part in parts:
            if getattr(part, "inline_data", None) is not None:
                data = getattr(part.inline_data, "data", None)
                if data:
                    image_bytes = data if isinstance(data, bytes) else data
                    break
            if getattr(part, "as_image", None) is not None:
                try:
                    img = part.as_image()
                    if img is not None:
                        output = BytesIO()
                        img.save(output, format="PNG")
                        image_bytes = output.getvalue()
                        break
                except Exception:
                    pass
        
        if image_bytes:
            from PIL import Image
            logger.info(f"Gemini 圖片生成成功，圖片大小: {len(image_bytes)} bytes")
            img = Image.open(BytesIO(image_bytes))
            output_buffer = BytesIO()
            img.save(output_buffer, format="JPEG")
            return output_buffer.getvalue()
            
        logger.warning("Gemini API 回應沒有圖片資料。response 結構: %s", type(response).__name__)
        return None
    except ImportError as e:
        logger.warning("google-genai 未安裝或缺少 types: %s", e)
        return None
    except Exception as e:
        logger.error(f"Gemini 圖片生成失敗: {e}", exc_info=True)
        return None
     
# ---------- OpenAI DALL-E ----------
OPENAI_DALLE_DEFAULT_MODEL = "dall-e-3" 

async def _openai_dalle_generate_image(
    prompt: str,
    user_id: int = None,
) -> str | None:
    """非同步呼叫 OpenAI DALL-E API 生成圖片。"""
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        return None

    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key)
    model = (os.getenv("OPENAI_DALLE_MODEL") or "").strip() or OPENAI_DALLE_DEFAULT_MODEL

    try:
        response = await client.images.generate(
            model=model,
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url
        return image_url
    except Exception as e:
        logger.error(f"OpenAI DALL-E 圖片生成失敗: {e}", exc_info=True)
        return None

# ---------- 統一入口 ----------
IMAGE_GEN_FALLBACK_MSG = "目前暫時無法生成圖片，請稍後再試。"

async def generate_image_by_keyword(
    keyword: str,
    user_id: int = None,
) -> bytes | None: # 回傳 bytes 方便 Telegram send_photo
    """
    根據關鍵字生成圖片。
    優先使用 Gemini，未設定或失敗時退回 OpenAI DALL-E。
    """
    prompt = _get_image_gen_prompt(user_id, keyword)
    image_provider = (os.getenv("AI_IMAGE_PROVIDER") or "").strip().lower()
    
    gemini_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    openai_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    logger.info(
        "圖片生成 API：GEMINI_API_KEY=%s, OPENAI_API_KEY=%s, AI_IMAGE_PROVIDER=%s",
        "已設定" if gemini_key else "未設定",
        "已設定" if openai_key else "未設定",
        image_provider or "(未設，預設先試 Gemini)",
    )
    
    # 優先使用 Gemini
    if gemini_key and (not image_provider or image_provider == "gemini"):
        logger.info(f"嘗試使用 Gemini 生成圖片，prompt: {prompt}")
        try:
            # Gemini 是同步 API，在 async context 中需用 to_thread 運行
            image_bytes = await asyncio.to_thread(_gemini_generate_image_sync, prompt)
            if image_bytes:
                return image_bytes
            logger.warning("Gemini 圖片生成未回傳有效圖片。")
        except ImportError:
            logger.warning("google-genai 套件未安裝，略過 Gemini 圖片生成")
        except Exception as e:
            logger.warning("Gemini 圖片生成錯誤: %s", e, exc_info=True)
    
    # 退回使用 OpenAI DALL-E
    if openai_key and (not image_provider or image_provider == "openai"):
        logger.info(f"嘗試使用 DALL-E 生成圖片，prompt: {prompt}")
        try:
            image_url = await _openai_dalle_generate_image(prompt, user_id)
            if image_url:
                # DALL-E 回傳 URL，需要下載轉換為 bytes
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.get(image_url)
                    response.raise_for_status() # 檢查 HTTP 錯誤
                    image_bytes = response.content
                    logger.info(f"DALL-E 圖片下載成功，大小: {len(image_bytes)} bytes")
                    from PIL import Image
                    img = Image.open(BytesIO(image_bytes))
                    output_buffer = BytesIO()
                    img.save(output_buffer, format="JPEG")
                    return output_buffer.getvalue()
            logger.warning("DALL-E 圖片生成未回傳有效圖片 URL。")
        except ImportError:
            logger.warning("openai 套件未安裝，略過 DALL-E 圖片生成")
        except Exception as e:
            logger.warning("OpenAI DALL-E 圖片生成錯誤: %s", e, exc_info=True)
    
    logger.warning(
        "未設定圖片生成 API Key 或所有嘗試都失敗。請在 .env 設定 GEMINI_API_KEY=你的金鑰（或 OPENAI_API_KEY），並用同一個環境執行 pip install -r requirements.txt。"
    )
    return None
