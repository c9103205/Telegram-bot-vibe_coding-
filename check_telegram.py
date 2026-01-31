#!/usr/bin/env python3
"""
診斷「無法連接 Telegram」的腳本。
執行：python check_telegram.py
會依序檢查：套件、Token、網路與 API。
"""

import os
import sys
from pathlib import Path

# 載入 .env（與 main.py 相同方式）
def _load_env():
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        env_path = Path(__file__).resolve().parent / ".env"
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())

_load_env()

def main():
    print("=" * 60)
    print("Telegram 連線診斷")
    print("=" * 60)

    # 1. 檢查 python-telegram-bot 是否已安裝
    print("\n[1] 檢查 python-telegram-bot 套件...")
    try:
        import telegram
        print(f"    ✓ 已安裝，版本: {getattr(telegram, '__version__', '未知')}")
    except ImportError as e:
        print(f"    ✗ 未安裝或無法匯入: {e}")
        print("\n    解決方式：在「目前用來執行的 Python 環境」安裝套件：")
        print("      pip install python-telegram-bot")
        print("    若出現 SSL 錯誤，請檢查網路/代理/憑證，或換網路再試。")
        sys.exit(1)

    # 2. 檢查 Token 是否存在與格式
    print("\n[2] 檢查 TELEGRAM_BOT_TOKEN...")
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("    ✗ 未設定 TELEGRAM_BOT_TOKEN")
        print("    請在專案目錄建立 .env，內容：TELEGRAM_BOT_TOKEN=你的Token")
        sys.exit(1)

    token = token.strip()
    if token.startswith('"') or token.startswith("'"):
        print("    ⚠ Token 前後不應有引號，請從 .env 移除引號")
        token = token.strip('"').strip("'")

    if ":" not in token or len(token) < 20:
        print(f"    ✗ Token 格式可能錯誤（長度 {len(token)}，應類似 123456789:ABCdef...）")
        print("    請到 @BotFather 重新取得 Token")
        sys.exit(1)
    print(f"    ✓ Token 已設定（長度 {len(token)}，格式正常）")

    # 3. 呼叫 Telegram API 測試連線與 Token
    print("\n[3] 測試連線 Telegram API (getMe)...")
    try:
        import asyncio
        from telegram import Bot
        async def test():
            bot = Bot(token=token)
            async with bot:
                return await bot.get_me()
        info = asyncio.run(test())
        print(f"    ✓ 連線成功！Bot 使用者名稱: @{info.username}")
    except Exception as e:
        print(f"    ✗ 連線失敗: {e}")
        if "Unauthorized" in str(e) or "401" in str(e):
            print("    可能原因：Token 錯誤或已失效，請到 @BotFather 用 /token 重新取得")
        elif "timed out" in str(e).lower() or "Connection" in str(e):
            print("    可能原因：網路無法連到 api.telegram.org（防火牆、代理、地區限制）")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("診斷完成：環境與 Token 正常，理論上可以連接 Telegram。")
    print("請執行: python main.py")
    print("=" * 60)

if __name__ == "__main__":
    main()
