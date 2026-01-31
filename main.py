#!/usr/bin/env python3
"""專案主程式：啟動 Telegram 自動回覆機器人。"""

import os
import sys
from pathlib import Path

from logic import get_reply

TELEGRAM_AVAILABLE = True
_IMPORT_ERROR: Exception | None = None


def _load_env() -> None:
    """載入 .env（從專案目錄載入，與執行時 cwd 無關）。"""
    env_path = Path(__file__).resolve().parent / ".env"
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
    except ImportError:
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())


try:
    from bot import run_bot
except Exception as exc:  # 包含 telegram 未安裝時的 ImportError
    TELEGRAM_AVAILABLE = False
    _IMPORT_ERROR = exc


def _local_simulation() -> None:
    """本地純文字模擬對話，不需要安裝 telegram。"""
    print("目前無法使用 Telegram（可能尚未安裝 python-telegram-bot）。")
    if _IMPORT_ERROR is not None:
        print(f"詳細錯誤：{_IMPORT_ERROR}")
    print("改為啟動本地模擬模式。輸入文字，我會回覆；輸入 'exit' 或 'quit' 結束。")
    while True:
        try:
            text = input("你：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n結束本地模擬。")
            break
        if text.lower() in {"exit", "quit"}:
            print("結束本地模擬。")
            break
        reply = get_reply(text)
        print(f"Bot：{reply}")


def main() -> None:
    """載入環境變數並啟動機器人或本地模擬。"""
    _load_env()
    token = os.getenv("TELEGRAM_BOT_TOKEN")

    if TELEGRAM_AVAILABLE:
        if not token:
            print("錯誤：請設定環境變數 TELEGRAM_BOT_TOKEN")
            print("方式一：建立 .env 檔案，內容為 TELEGRAM_BOT_TOKEN=你的機器人Token")
            print("方式二：執行時設定：TELEGRAM_BOT_TOKEN=你的Token python main.py")
            sys.exit(1)

        run_bot(token)
    else:
        _local_simulation()


if __name__ == "__main__":
    main()
