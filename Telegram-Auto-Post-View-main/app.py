import os
import threading
import subprocess
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Конфигурация ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
ALLOWED_USER_ID = int(os.environ.get("MY_USER_ID", 0)) # Сюда впишете ваш ID

# --- Flask (чтобы Render не убивал процесс) ---
app = Flask(__name__)

@app.route('/')
@app.route('/health')
def health():
    return "Bot is running", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- Логика бота ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID:
        await update.message.reply_text("Нет доступа.")
        return
    await update.message.reply_text(
        "Пришли мне ссылку на пост в формате:\n"
        "`https://t.me/имя_канала/номер_поста`\n"
        "Например: `https://t.me/Uzusto_uz/14`"
    )

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ALLOWED_USER_ID:
        return

    text = update.message.text
    if "t.me/" not in text:
        await update.message.reply_text("Это не похоже на ссылку.")
        return

    # Парсим ссылку
    try:
        parts = text.split("t.me/")[1].split("/")
        channel = parts[0]
        post = parts[1]
    except:
        await update.message.reply_text("Не могу разобрать ссылку.")
        return

    await update.message.reply_text(f"Запускаю накрутку для @{channel}, пост {post}. Ждите...")

    # Запускаем teleview.py в отдельном процессе
    # Важно: файл teleview.py должен лежать в той же папке
    try:
        subprocess.Popen(
            ["python", "teleview.py", "--mode", "auto", "--channel", channel, "--post", post],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception as e:
        await update.message.reply_text(f"Ошибка запуска: {e}")

def main():
    # Запускаем Flask в фоне
    threading.Thread(target=run_flask, daemon=True).start()

    # Запускаем бота
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    
    print("Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()
