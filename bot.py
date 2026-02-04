#!/usr/bin/env python3
"""Telegram 自動回覆機器人。"""

import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
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
from ai_reply import get_ai_reply, GIRLFRIEND_PERSONALITIES, save_user_config, _load_user_config

# 對話狀態定義
CHOOSING_GIRLFRIEND = 1
ENTERING_NAME = 2
CONFIRMING = 3


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """處理 /start 指令，引導用戶選擇女友類型。"""
    user = update.effective_user
    user_config = _load_user_config(user.id)
    
    # 如果已經配置過，直接顯示歡迎訊息
    if user_config.get("girlfriend_type") and user_config.get("user_name"):
        girlfriend_name = user_config.get("girlfriend_name", "寶貝")
        girlfriend_type = user_config.get("girlfriend_type")
        girlfriend_type_name = GIRLFRIEND_PERSONALITIES.get(girlfriend_type, {}).get("name", "女友")
        
        await update.message.reply_text(
            f"歡迎回來，{user_config.get('user_name')}！💕\n\n"
            f"我是你的女友 {girlfriend_name}（{girlfriend_type_name}）。\n\n"
            f"想要更改設定嗎？使用 /reset 重新配置。"
        )
        return ConversationHandler.END
    
    # 新用戶，開始配置流程
    keyboard = [
        [InlineKeyboardButton("👧 溫柔可愛的女高中生", callback_data='girlfriend_highschool')],
        [InlineKeyboardButton("👩‍🦰 成熟姊姊", callback_data='girlfriend_mature')],
        [InlineKeyboardButton("😏 咸濕姐姐", callback_data='girlfriend_spicy')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"嗨 {user.mention_html()}！👋\n\n"
        f"歡迎來到女友機器人！請選擇你想要的女友類型呢？💕",
        reply_markup=reply_markup,
        parse_mode="HTML",
    )
    
    return CHOOSING_GIRLFRIEND


async def choose_girlfriend(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """處理用戶選擇女友類型。"""
    query = update.callback_query
    await query.answer()
    
    # 提取女友類型
    girlfriend_type = query.data.replace('girlfriend_', '')
    context.user_data['girlfriend_type'] = girlfriend_type
    
    girlfriend_type_name = GIRLFRIEND_PERSONALITIES[girlfriend_type]['name']
    
    await query.edit_message_text(
        text=f"你選擇了：{girlfriend_type_name} 💕\n\n"
        f"接下來，請告訴我你的名字吧，親愛的～ 💫"
    )
    
    return ENTERING_NAME


async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """處理用戶輸入名字。"""
    user = update.effective_user
    user_name = update.message.text.strip()
    
    if not user_name or len(user_name) > 20:
        await update.message.reply_text(
            "名字太長或為空呢😅 請輸入 1～20 個字的名字～"
        )
        return ENTERING_NAME
    
    context.user_data['user_name'] = user_name
    
    # 讓用戶選擇女友的名字（可選）
    girlfriend_type = context.user_data.get('girlfriend_type', 'highschool')
    girlfriend_type_name = GIRLFRIEND_PERSONALITIES[girlfriend_type]['name']
    
    keyboard = [
        [InlineKeyboardButton("使用預設名字（寶貝）", callback_data='use_default_name')],
        [InlineKeyboardButton("自訂女友名字", callback_data='custom_girlfriend_name')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"好的，{user_name}！💕\n\n"
        f"你選的女友是 {girlfriend_type_name}。\n"
        f"要給她起個名字嗎？還是用預設的『寶貝』呢？",
        reply_markup=reply_markup,
    )
    
    return CONFIRMING


async def confirm_default_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """使用預設女友名字。"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    user_name = context.user_data.get('user_name', '親愛的')
    girlfriend_type = context.user_data.get('girlfriend_type', 'highschool')
    girlfriend_name = '寶貝'
    
    # 保存配置
    config = {
        "girlfriend_type": girlfriend_type,
        "girlfriend_name": girlfriend_name,
        "user_name": user_name,
    }
    save_user_config(user.id, config)
    
    girlfriend_type_name = GIRLFRIEND_PERSONALITIES[girlfriend_type]['name']
    
    await query.edit_message_text(
        text=f"完美！✨\n\n"
        f"現在我是你的女友 {girlfriend_name}（{girlfriend_type_name}）。\n"
        f"很高興認識你，{user_name}！💕\n\n"
        f"開始聊天吧～ 任何時候想改設定都可以用 /reset 喔！"
    )
    
    return ConversationHandler.END


async def custom_girlfriend_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """引導用戶輸入自訂女友名字。"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        text="好呀～ 那就告訴我，你想給我起什麼名字呢？😊"
    )
    
    context.user_data['waiting_for_girlfriend_name'] = True
    return CONFIRMING


async def process_girlfriend_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """處理自訂女友名字。"""
    if not context.user_data.get('waiting_for_girlfriend_name'):
        # 這是普通聊天訊息，不是女友名字
        return await auto_reply(update, context)
    
    user = update.effective_user
    girlfriend_name = update.message.text.strip()
    
    if not girlfriend_name or len(girlfriend_name) > 20:
        await update.message.reply_text(
            "名字太長或為空呢😅 請輸入 1～20 個字的名字～"
        )
        return CONFIRMING
    
    user_name = context.user_data.get('user_name', '親愛的')
    girlfriend_type = context.user_data.get('girlfriend_type', 'highschool')
    
    # 保存配置
    config = {
        "girlfriend_type": girlfriend_type,
        "girlfriend_name": girlfriend_name,
        "user_name": user_name,
    }
    save_user_config(user.id, config)
    
    girlfriend_type_name = GIRLFRIEND_PERSONALITIES[girlfriend_type]['name']
    
    await update.message.reply_text(
        f"完美！✨\n\n"
        f"現在我是你的女友 {girlfriend_name}（{girlfriend_type_name}）。\n"
        f"很高興認識你，{user_name}！💕\n\n"
        f"開始聊天吧～ 任何時候想改設定都可以用 /reset 喔！"
    )
    
    context.user_data.clear()
    return ConversationHandler.END


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """重設用戶配置，重新開始選擇女友。"""
    await update.message.reply_text("好的，讓我們重新開始吧～")
    # 清空用戶資料並重新開始
    context.user_data.clear()
    return await start(update, context)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """處理 /help 指令。"""
    await update.message.reply_text(
        "可用的指令：\n"
        "/start - 開始或查看當前配置\n"
        "/reset - 重新選擇女友和姓名\n"
        "/help - 顯示此訊息\n\n"
        "傳送任意訊息給我，我會用 AI 回覆你～ 💕"
    )


async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """對所有文字訊息自動回覆：優先 AI，失敗或未設定則用關鍵字回覆。"""
    if not update.message:
        logger.warning("auto_reply: update.message 為空，略過")
        return
    
    user_id = update.effective_user.id
    text = update.message.text or ""
    
    try:
        reply = await get_ai_reply(text, user_id)
        if reply is None:
            reply = get_reply(text)
        await update.message.reply_text(reply)
        logger.info("回覆使用者 %s: %s", user_id, (reply[:50] + "..." if len(reply) > 50 else reply))
    except Exception as e:
        logger.exception("auto_reply 發生錯誤: %s", e)
        try:
            await update.message.reply_text("回覆時發生錯誤，請稍後再試。")
        except Exception:
            pass


def run_bot(token: str) -> None:
    """建立並啟動 Bot。"""
    application = Application.builder().token(token).build()

    # 設置對話處理器
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_GIRLFRIEND: [
                CallbackQueryHandler(choose_girlfriend, pattern='^girlfriend_')
            ],
            ENTERING_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_name)
            ],
            CONFIRMING: [
                CallbackQueryHandler(confirm_default_name, pattern='^use_default_name$'),
                CallbackQueryHandler(custom_girlfriend_name, pattern='^custom_girlfriend_name$'),
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    process_girlfriend_name
                ),
            ],
        },
        fallbacks=[CommandHandler("reset", reset)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("reset", reset))
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
