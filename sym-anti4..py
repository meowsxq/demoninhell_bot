from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (Application, CommandHandler, MessageHandler, filters, ContextTypes)
import time
import asyncio
import random

COOLDOWN_TIME = 4
MAX_GROUPS = 2
user_forwarding_groups = {}
last_message_time = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = (
        "<b>👋 Привет, мой маленький приспешник!</b> \n\n"
        "Я здесь, чтобы помочь тебе отправлять сообщения в группы от имени бота.\n\n"
        "🔹 <b>Используй команду</b> /sendmsg <i>[ид группы]</i>, чтобы отправить сообщение в группу, где состоит бот.\n\n"
        "📢 <b>Примечание:</b> Убедитесь, что бот добавлен в группу перед отправкой сообщения."
        "\n\n"
        "🔗 <b>😈Демонесса:</b> <a href='https://t.me/demonic_Girlll'>ТЫК</a>\n\n"
    )
    await update.message.reply_text(message, parse_mode='HTML')

    keyboard = [
        [InlineKeyboardButton("👉 ЖМИ СЮДА!", url="https://t.me/demoninhellnew_bot?startgroup=true")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Добавь меня в чат", reply_markup=reply_markup)

    custom_keyboard = [
        [KeyboardButton("Помощь"), KeyboardButton("Bug?"),KeyboardButton("Используемые чаты"), KeyboardButton("Стикеры")]
    ]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard, resize_keyboard=True)
    #await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)

async def sendmsg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id, args = update.message.from_user.id, context.args
    user_forwarding_groups.setdefault(user_id, set())
    
    if not args: 
        return await update.message.reply_text('Использование: /sendmsg [ид группы]')
    
    try:
        group_id = int(args[0])
        chat = await context.bot.get_chat(group_id)
        if chat.type not in {'group', 'supergroup'}:
            return await update.message.reply_text('Указанный ID не является группой.')
    except Exception:
        return await update.message.reply_text('Бот не состоит в указанной группе или группа не существует.')
    
    if group_id in user_forwarding_groups[user_id]:
        user_forwarding_groups[user_id].discard(group_id)
        message = f'Пересылка сообщений для группы {group_id} отключена.'
    elif len(user_forwarding_groups[user_id]) < MAX_GROUPS:
        user_forwarding_groups[user_id].add(group_id)
        message = f'Пересылка сообщений для группы {group_id} включена.'
    else:
        return await update.message.reply_text('Вы не можете подключить более 2 групп.')

    await update.message.reply_text(message)

async def lists_groups(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id in user_forwarding_groups and user_forwarding_groups[user_id]:
        groups_list = "\n".join(str(group_id) for group_id in user_forwarding_groups[user_id])
        await update.message.reply_text(f"Подключенные группы:\n{groups_list}")
    else:
        await update.message.reply_text("Нет подключенных групп.")

async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user 
    user_id = user.id
    if user_id not in user_forwarding_groups:
        user_forwarding_groups[user_id] = set()

    global last_message_time
    current_time = time.time()

    if user_id in last_message_time: 
        if current_time - last_message_time[user_id] < COOLDOWN_TIME:
            await update.message.reply_text(f"Вы отправляете сообщения слишком быстро. Пожалуйста, подождите немного.")
            return

    last_message_time[user_id] = current_time

    if user_forwarding_groups[user_id]:
        tasks = []
        if update.message.text:
            tasks.extend([context.bot.send_message(chat_id=group_id, text=update.message.text) for group_id in user_forwarding_groups[user_id]])
        elif update.message.photo:
            tasks.extend([context.bot.send_photo(chat_id=group_id, photo=update.message.photo[-1].file_id,
                                                 caption=update.message.caption) for group_id in user_forwarding_groups[user_id]])
        elif update.message.video:
            tasks.extend([context.bot.send_video(chat_id=group_id, video=update.message.video.file_id,
                                                 caption=update.message.caption) for group_id in user_forwarding_groups[user_id]])
        elif update.message.document:
            tasks.extend([context.bot.send_document(chat_id=group_id, document=update.message.document.file_id,
                                                    caption=update.message.caption) for group_id in user_forwarding_groups[user_id]])
        elif update.message.audio:
            tasks.extend([context.bot.send_audio(chat_id=group_id, audio=update.message.audio.file_id,
                                                 caption=update.message.caption) for group_id in user_forwarding_groups[user_id]])
        elif update.message.sticker:
            tasks.extend([context.bot.send_sticker(chat_id=group_id, sticker=update.message.sticker.file_id) for group_id in user_forwarding_groups[user_id]])
        elif update.message.voice:
            tasks.extend([context.bot.send_voice(chat_id=group_id, voice=update.message.voice.file_id,
                                                 caption=update.message.caption) for group_id in user_forwarding_groups[user_id]])
        elif update.message.poll:
            question = update.message.poll.question
            options = [option.text for option in update.message.poll.options]
            tasks.extend([context.bot.send_poll(chat_id=group_id, question=question, options=options,
                                                is_anonymous=update.message.poll.is_anonymous,
                                                allows_multiple_answers=update.message.poll.allows_multiple_answers) for group_id in user_forwarding_groups[user_id]])

        await asyncio.gather(*tasks)
    else:
        await update.message.reply_text("У вас не подключены группы.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = (
        "<b>🛠️ Доступные команды:</b>\n\n"
        "🔹 <b>/start</b> - 🚀 <i>Начать работу с ботом</i>\n\n"
        "🔹 <b>/sendmsg [ид группы]</b> - 🔄 <i>Включить/выключить пересылку сообщений для указанной группы</i>\n\n"
        "⚙️ <i>Узнай id группы:</i> @username_to_id_bot\n\n"
    )
    await update.message.reply_text(message, parse_mode='HTML')

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Команда не найдена!')

with open('sticker.txt', 'r') as file:
    stickers = [line.strip() for line in file.readlines()]

async def send_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if stickers:
        sticker_ids = random.sample(stickers, min(3, len(stickers)))
        tasks = [context.bot.send_sticker(chat_id=update.message.chat_id, sticker=sticker_id) for sticker_id in sticker_ids]
        await asyncio.gather(*tasks)
    else:
        await update.message.reply_text('Список стикеров пуст.')

async def sticker_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    sticker = update.message.sticker
    if sticker:
        await update.message.reply_text(f'ID стикера: {sticker.file_id}')
    else:
        await update.message.reply_text('Это не стикер.')

async def creator_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("За багами или вопросами: @w1_w1_w1_w1")

def main() -> None:
    app = Application.builder().token("7119691423:AAGSYh3YUTiw-nDECLCnw37loGOArBbYk9M").connection_pool_size(256).build()
    app.add_handler(CommandHandler("start", start, filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("sendmsg", sendmsg, filters.ChatType.PRIVATE))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.Text(["Bug?"]), creator_info))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.Text(["Помощь"]), help_command))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.Text(["Стикеры"]), send_sticker))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.Text(["Используемые чаты"]), lists_groups))
    app.add_handler(MessageHandler(filters.Sticker.ALL, sticker_id))
    app.add_handler(MessageHandler(filters.COMMAND & filters.ChatType.PRIVATE, unknown_command))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE, forward_message))
    app.run_polling()

if __name__ == '__main__':
    main()