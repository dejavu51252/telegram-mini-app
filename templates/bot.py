import logging
import os
import sqlite3
from threading import Thread
from flask import Flask, render_template, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# --- 1. ВЕБ-СЕРВЕР (FLASK) ДЛЯ RENDER И 24/7 ---
web_app = Flask(__name__)

@web_app.route('/')
def index():
    # Отправляет HTML-файл из папки templates (Telegram Mini App)
    return render_template('index.html')

@web_app.route('/submit', methods=['POST'])
def submit_order():
    data = request.json
    user_id = data.get('user_id')
    service = data.get('service')

    # Сохраняем заказ в базу данных SQLite
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            service TEXT
        )
    ''')
    cursor.execute("INSERT INTO orders (user_id, service) VALUES (?, ?)", (user_id, service))
    conn.commit()
    conn.close()

    print(f"📥 Новый заказ от пользователя {user_id}: {service}")
    return jsonify({"status": "success"})

def run_web():
    port = int(os.environ.get('PORT', 8080))
    web_app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.daemon = True
    t.start()

# --- 2. НАСТРОЙКА TELEGRAM БОТА ---
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ссылка на твой сайт на Render (автоматически подтянется из переменной окружения WEB_APP_URL)
    web_app_url = os.environ.get("WEB_APP_URL", "https://tvoj-proekt.onrender.com")
    
    keyboard = [
        [InlineKeyboardButton("🚀 Открыть Mini App каталог", web_app=WebAppInfo(url=web_app_url))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Привет! Нажми на кнопку ниже, чтобы открыть каталог услуг в Telegram Mini App:",
        reply_markup=reply_markup
    )

# --- 3. ЗАПУСК ---
if __name__ == '__main__':
    keep_alive()  # Запускаем Flask-сервер в фоновом потоке для Render
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    print("🤖 Telegram Mini App бот запущен!")
    app.run_polling()
