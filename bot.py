#!/usr/bin/env python3
"""Telegram 自動回覆機器人。"""

import os
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# 日誌設定
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

from logic import get_reply
from ai_reply import get_ai_reply


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """處理 /start 指令。"""
    user = update.effective_user
    await update.message.reply_text(
        f"嗨 {user.mention_html()}！我是自動回覆機器人，傳送任何訊息我都會回覆。",
        parse_mode="HTML",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """處理 /help 指令。"""
    await update.message.reply_text(
        "傳送任意文字給我，我會用 Gemini AI 回覆。\n"
        "（若未設定 GEMINI_API_KEY，則使用關鍵字回覆）"
    )


async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """對所有文字訊息自動回覆：優先 AI，失敗或未設定則用關鍵字回覆。"""
    if not update.message:
        logger.warning("auto_reply: update.message 為空，略過")
        return
    text = update.message.text or ""
    try:
        reply = await get_ai_reply(text)
        if reply is None:
            reply = get_reply(text)
        await update.message.reply_text(reply)
        logger.info("回覆使用者 %s: %s", update.effective_user.id, (reply[:50] + "..." if len(reply) > 50 else reply))
    except Exception as e:
        logger.exception("auto_reply 發生錯誤: %s", e)
        try:
            await update.message.reply_text("回覆時發生錯誤，請稍後再試。")
        except Exception:
            pass


def run_bot(token: str) -> None:
    """建立並啟動 Bot。"""
    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, auto_reply)
    )

    logger.info("機器人啟動中...")
    logger.info("按 Ctrl+C 可停止機器人")
    if os.getenv("GEMINI_API_KEY", "").strip():
        logger.info("GEMINI_API_KEY 已設定，將使用 Gemini 回覆")
    else:
        logger.info("GEMINI_API_KEY 未設定，將使用關鍵字回覆")
    
    try:
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True,  # 啟動時忽略舊訊息
        )
    except KeyboardInterrupt:
        logger.info("收到停止訊號，正在關閉機器人...")
    except Exception as e:
        logger.error("機器人發生錯誤: %s", e, exc_info=True)
        raise
    finally:
        logger.info("機器人已停止")
