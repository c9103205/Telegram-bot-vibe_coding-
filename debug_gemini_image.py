#!/usr/bin/env python3
"""
單獨測試 Gemini 圖片生成 API，不經過 Telegram。
執行：python debug_gemini_image.py
會載入 .env、呼叫圖片生成、存檔或印出完整錯誤。
"""

import os
import sys
from pathlib import Path

def _load_env():
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

_load_env()


def main():
    print("=" * 60)
    print("Gemini 圖片生成 API 除錯")
    print("=" * 60)

    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        print("\n[錯誤] 未設定 GEMINI_API_KEY")
        sys.exit(1)

    from ai_image_gen import _gemini_generate_image_sync, GEMINI_IMAGE_DEFAULT_MODEL
    model = (os.getenv("GEMINI_IMAGE_MODEL") or "").strip() or GEMINI_IMAGE_DEFAULT_MODEL
    print(f"\n[1] 使用模型: {model}")
    print("[2] 測試 prompt: 一隻可愛的貓咪")
    print("[3] 呼叫 Gemini 圖片生成...")
    print("-" * 60)

    try:
        image_bytes = _gemini_generate_image_sync("一隻可愛的貓咪")
        if image_bytes:
            out_path = Path(__file__).resolve().parent / "debug_generated_image.jpg"
            with open(out_path, "wb") as f:
                f.write(image_bytes)
            print(f"成功！圖片已儲存至: {out_path}")
        else:
            print("API 有回應但未取得圖片內容（請看上方日誌）。")
    except Exception as e:
        print(f"錯誤: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        print("-" * 60)
        print("若為 404：此模型在你地區可能不可用，可於 .env 設 GEMINI_IMAGE_MODEL=gemini-2.5-flash-image 再試。")
        print("若為 429：配額用盡，請稍後或隔日再試。")
        sys.exit(1)


if __name__ == "__main__":
    main()
