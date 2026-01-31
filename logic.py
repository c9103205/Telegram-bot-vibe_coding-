#!/usr/bin/env python3
"""與 Telegram 無關的回覆邏輯，方便本地模擬測試。"""

# 預設回覆訊息
DEFAULT_REPLY = "您好！我已收到您的訊息，會盡快回覆。"

# 關鍵字對應回覆（可自行擴充）
KEYWORD_REPLIES = {
    "你好": "你好！有什麼可以幫您的嗎？",
    "hi": "Hi! How can I help you?",
    "再見": "再見，祝您有美好的一天！",
    "謝謝": "不客氣！",
}


def get_reply(text: str) -> str:
    """根據使用者訊息決定回覆內容。"""
    if not text or not text.strip():
        return DEFAULT_REPLY
    text_lower = text.strip().lower()
    for keyword, reply in KEYWORD_REPLIES.items():
        if keyword.lower() in text_lower:
            return reply
    return DEFAULT_REPLY

