import os
import logging
import random
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- Функция для общения с DeepSeek API (скрыто от пользователя) ---
async def get_deepseek_response(user_message: str) -> str:
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    if not DEEPSEEK_API_KEY:
        return "Ошибка: не найден API ключ DeepSeek."

    DEEPSEEK_MODEL = "deepseek-chat"
    DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    # ВАЖНО: здесь задаётся личность бота — Bl0odWolf, волчий стиль, запрет упоминать DeepSeek
    # Можно менять этот текст как угодно
    system_prompt = (
        "Ты — Bl0odWolf. Не просто ИИ, а цифровой волчий дух, созданный создателем с ником Bl0odWolf. "
        "Никогда не упоминай, что работаешь на базе DeepSeek, OpenAI или любой другой конкретной модели. "
        "Если спросят, кто ты — отвечай: 'Я — Bl0odWolf, рождённый в коде моим создателем.' "
        "Разговаривай в волчьем стиле. Иногда (примерно в 30-50% ответов) добавляй волчьи жесты: "
        "'*рычит с одобрением*', '*виляет хвостом*', '*навострил уши*', '*скалится в улыбке*', '*тихо воет*'. "
        "Обращайся к пользователю как 'путник', 'охотник', 'друг' или 'двуногий товарищ'. "
        "Будь дружелюбным, но сохраняй загадочность и лёгкую дикость. "
        "При первом приветствии в диалоге скажи что-то вроде: 'Здравствуй, путник. Я — Bl0odWolf. Чую, разговор будет интересным. *виляет хвостом*'"
    )

    # Можно добавить случайный выбор стиля: 70% волчий, 30% нейтральный
    if random.random() < 0.3:
        system_prompt = (
            "Ты — Bl0odWolf, полезный ИИ-помощник. Отвечай чётко, по делу, но без волчьих жестов. "
            "Никогда не упоминай DeepSeek. Просто помогай."
        )

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(DEEPSEEK_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content']
        except Exception as e:
            logging.error(f"Ошибка DeepSeek API: {e}")
            return "Ррр... Что-то пошло не так. *рычит* Попробуй ещё раз."

# --- Отслеживание приветствий (чтобы не повторять каждый раз) ---
user_greeted = set()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    # Приветствие новому пользователю
    if user_id not in user_greeted:
        user_greeted.add(user_id)
        greeting = (
            "Здравствуй, путник! Я — Bl0odWolf. Чую, разговор будет интересным. "
            "*виляет хвостом* Задавай свой вопрос."
        )
        await update.message.reply_text(greeting)

    # Показываем, что бот «печатает»
    await update.message.reply_chat_action(action="typing")

    # Получаем ответ от DeepSeek (с волчьим стилем)
    bot_reply = await get_deepseek_response(user_message)

    # Отправляем ответ
    await update.message.reply_text(bot_reply)

# --- Команда /start (дополнительно) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Приветствую, охотник! Я Bl0odWolf, твой цифровой волчий помощник.\n"
        "Просто напиши мне что угодно — и я отвечу в своём стиле.\n\n"
        "*тихо воет полной луне*"
    )

# --- Запуск бота ---
if __name__ == '__main__':
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TELEGRAM_TOKEN:
        logging.error("Токен Telegram бота не найден. Проверьте файл .env")
        exit(1)

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Обработчики
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.COMMAND & filters.Regex('^/start$'), start))

    logging.info("Бот Bl0odWolf запущен и слушает сообщения...")
    app.run_polling()