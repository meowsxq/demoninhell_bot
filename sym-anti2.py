from telegram import Update, Poll
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import time
import asyncio
forwarding_groups = set()
last_message_time = {}
COOLDOWN_TIME = 4
message_count = 0
async def log_message(user, message_type, context: ContextTypes.DEFAULT_TYPE) -> None:
    global message_count
    message_count += 1
    user_info = f"{user.first_name or ''} {user.last_name or ''} ({user.username or 'без юзернейма'})".strip()
    print(f"Сообщение #{message_count} от пользователя {user_info}: {message_type}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = (
        "👋 Привет, мой маленький приспешник!\n\n"
        "Я здесь, чтобы помочь тебе отправлять сообщения в группы от имени бота.\n\n"
        "🔹 Используй команду /sendmsg [ид группы], чтобы отправить сообщение в группу, где состоит бот.\n"
        "🔹 Если что-то не понятно, просто напиши /help и я помогу тебе.\n\n"
    )
    await update.message.reply_text(message)
    
async def sendmsg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text('Использование: /sendmsg [ид группы]')
        return
    try:
        group_id = int(context.args[0])
        message = f'Пересылка сообщений для группы {group_id} {"отключена" if group_id in forwarding_groups else "включена"}.'
        forwarding_groups.discard(group_id) if group_id in forwarding_groups else forwarding_groups.add(group_id)
        await update.message.reply_text(message)
    except ValueError:
        await update.message.reply_text('Неправильный формат ид группы.')

async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global last_message_time

    user = update.message.from_user
    current_time = time.time()

    if user.id in last_message_time:
        if current_time - last_message_time[user.id] < COOLDOWN_TIME:
            await update.message.reply_text(f"Вы отправляете сообщения слишком быстро. Пожалуйста, подождите немного. {COOLDOWN_TIME}сек")
            return

    last_message_time[user.id] = current_time

    if forwarding_groups:
        tasks = []
        if update.message.text:
            tasks.extend([context.bot.send_message(chat_id=group_id, text=update.message.text) for group_id in forwarding_groups])
            await log_message(user, "Текстовое сообщение", context)
        elif update.message.photo:
            tasks.extend([context.bot.send_photo(chat_id=group_id, photo=update.message.photo[-1].file_id,
                                                 caption=update.message.caption) for group_id in forwarding_groups])
            await log_message(user, "Фото сообщение", context)
        elif update.message.video:
            tasks.extend([context.bot.send_video(chat_id=group_id, video=update.message.video.file_id,
                                                 caption=update.message.caption) for group_id in forwarding_groups])
            await log_message(user, "Видео сообщение", context)
        elif update.message.document:
            tasks.extend([context.bot.send_document(chat_id=group_id, document=update.message.document.file_id,
                                                    caption=update.message.caption) for group_id in forwarding_groups])
            await log_message(user, "Документ сообщение", context)
        elif update.message.audio:
            tasks.extend([context.bot.send_audio(chat_id=group_id, audio=update.message.audio.file_id,
                                                 caption=update.message.caption) for group_id in forwarding_groups])
            await log_message(user, "Аудио сообщение", context)
        elif update.message.sticker:
            tasks.extend([context.bot.send_sticker(chat_id=group_id, sticker=update.message.sticker.file_id) for group_id in forwarding_groups])
            await log_message(user, "Стикер сообщение", context)
        elif update.message.voice:
            tasks.extend([context.bot.send_voice(chat_id=group_id, voice=update.message.voice.file_id,
                                                 caption=update.message.caption) for group_id in forwarding_groups])
            await log_message(user, "Голосовое сообщение", context)
        elif update.message.poll:
            question = update.message.poll.question
            options = [option.text for option in update.message.poll.options]
            tasks.extend([context.bot.send_poll(chat_id=group_id, question=question, options=options,
                                                is_anonymous=update.message.poll.is_anonymous,
                                                allows_multiple_answers=update.message.poll.allows_multiple_answers) for group_id in forwarding_groups])
            await log_message(user, "Опрос", context)

        await asyncio.gather(*tasks)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"Всего сообщений переслано: {message_count}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = (
        "🛠️ Доступные команды:\n\n"
        "🔹 /start - Начать работу с ботом\n"
        "🔹 /stats - Показать статистику пересланных сообщений\n"
        "🔹 /sendmsg [ид группы] - Включить/выключить пересылку сообщений для указанной группы\n\n"
        "ℹ️ Ид группы можно узнать, обратившись к боту: @username_to_id_bot\n\n"
    )
    await update.message.reply_text(message)
    
async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Команда не найдена, введите /help')

def main() -> None:
    app = Application.builder().token("7101128831:AAHz5zawi_v0ILZYyfSLAd1lhC4a6o38psU").build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sendmsg", sendmsg))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE, forward_message))
    app.run_polling()

if __name__ == '__main__':
    main()