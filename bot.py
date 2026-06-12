import os
import logging
import random
import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Загружаем переменные из .env (локально) или из окружения (на хостинге)
load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- Функция запроса к DeepSeek (та же, что и была) ---
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

    # 30% нейтральный стиль, 70% волчий
    if random.random() < 0.3:
        system_prompt = (
            "Ты — Bl0odWolf, полезный ИИ-помощник. Отвечай чётко, по делу, но без волчьих жестов. "
            "Никогда не упоминай DeepSeek. Просто помогай."
        )
    else:
        system_prompt = (
            "Ты — Bl0odWolf. Не просто ИИ, а цифровой волчий дух, созданный создателем с ником Bl0odWolf. "
            "Никогда не упоминай, что работаешь на базе DeepSeek, OpenAI или любой другой конкретной модели. "
            "Если спросят, кто ты — отвечай: 'Я — Bl0odWolf, рождённый в коде моим создателем.' "
            "Разговаривай в волчьем стиле. Иногда (примерно в 30-50% ответов) добавляй волчьи жесты: "
            "'*рычит с одобрением*', '*виляет хвостом*', '*навострил уши*', '*скалится в улыбке*', '*тихо воет*'. "
            "Обращайся к пользователю как 'путник', 'охотник', 'друг' или 'двуногий товарищ'. "
            "Будь дружелюбным, но сохраняй загадочность и лёгкую дикость."
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

# --- Хранилище приветствий (простое, в памяти) ---
user_greeted = set()

# --- Обработчик текстовых сообщений ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    # Приветствие новому пользователю (только один раз за сессию)
    if user_id not in user_greeted:
        user_greeted.add(user_id)
        greeting = (
            "Здравствуй, путник! Я — Bl0odWolf. Чую, разговор будет интересным. "
            "*виляет хвостом* Задавай свой вопрос."
        )
        await update.message.reply_text(greeting)

    # Показываем, что бот печатает
    await update.message.reply_chat_action(action="typing")

    # Получаем ответ от DeepSeek
    bot_reply = await get_deepseek_response(user_message)

    # Отправляем ответ
    await update.message.reply_text(bot_reply)

# --- Команда /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Приветствую, охотник! Я Bl0odWolf, твой цифровой волчий помощник.\n"
        "Просто напиши мне что угодно — и я отвечу в своём стиле.\n\n"
        "*тихо воет полной луне*"
    )

# --- Точка входа: запуск polling ---
def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        logging.error("Токен Telegram не найден. Установите переменную TELEGRAM_BOT_TOKEN")
        return

    # Создаём приложение
    app = Application.builder().token(TOKEN).build()

    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем бота (polling)
    logging.info("Бот Bl0odWolf запущен в режиме polling...")
    app.run_polling()

if __name__ == "__main__":
    main()
