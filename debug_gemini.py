#!/usr/bin/env python3
"""
單獨測試 Gemini API，不經過 Telegram。
執行：python debug_gemini.py
會載入 .env、呼叫 Gemini、印出回覆或完整錯誤，方便排查失效原因。
"""

import os
import sys
from pathlib import Path

# 載入 .env（與 main.py 相同）
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
    print("Gemini API 除錯")
    print("=" * 60)

    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        print("\n[錯誤] 未設定 GEMINI_API_KEY")
        print("請在 .env 加上一行：GEMINI_API_KEY=你的金鑰")
        print("金鑰可到 https://aistudio.google.com/app/apikey 取得")
        sys.exit(1)

    # 不印出完整 key，只顯示前後幾碼
    key_preview = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
    print(f"\n[1] GEMINI_API_KEY 已設定（{key_preview}）")

    model = (os.getenv("GEMINI_MODEL") or "").strip() or "gemini-2.0-flash"
    print(f"[2] 使用模型: {model}")

    test_message = "你好，請用一句話介紹你自己。"
    print(f"[3] 測試訊息: {test_message}")
    print("\n[4] 呼叫 Gemini API...")
    print("-" * 60)

    try:
        from google import genai
    except ImportError as e:
        print(f"\n[錯誤] 無法匯入 google.genai: {e}")
        print("請在「你用來跑 main.py 的同一個環境」執行：")
        print("  pip install google-genai")
        print("有虛擬環境請先：source venv/bin/activate")
        sys.exit(1)

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model,
            contents=test_message,
        )
        text = getattr(response, "text", None)
        if text and text.strip():
            print("回覆成功：")
            print(text.strip())
            print("-" * 60)
            print("若這裡有回覆但 Telegram 沒有，問題可能在 bot 流程或日誌等級。")
        else:
            print("API 有回應但沒有文字內容。")
            print("response 內容:", response)
    except Exception as e:
        print("API 呼叫失敗：")
        print(type(e).__name__, ":", e)
        print()
        import traceback
        traceback.print_exc()
        print("-" * 60)
        print("常見原因：")
        print("  - 429 RESOURCE_EXHAUSTED → 免費配額用盡，等幾分鐘或隔日再試；到 https://ai.dev/rate-limit 查看用量")
        print("  - API 金鑰錯誤或過期 → 到 AI Studio 重新建立")
        print("  - 模型名稱錯誤 → 檢查 GEMINI_MODEL（預設 gemini-2.0-flash）")
        print("  - 網路連線問題 → 檢查防火牆、代理")
        sys.exit(1)

    print("\n除錯結束。")


if __name__ == "__main__":
    main()
