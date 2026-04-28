import os
import asyncio
import random
import logging
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route
from starlette.requests import Request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- Логирование для отладки на Render ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Конфигурация из переменных окружения ---
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("Переменная TELEGRAM_BOT_TOKEN не установлена")
WEBHOOK_URL = os.environ.get("RENDER_EXTERNAL_URL")
if not WEBHOOK_URL:
    raise ValueError("Переменная RENDER_EXTERNAL_URL не установлена (должна подставиться автоматически на Render)")
PORT = int(os.getenv("PORT", 8000))

# --- Ваши данные (угрозы и дыхательные практики) ---
THREATS = {
    "Соцсети (залипание)": "Протокол: Блокировка приложений 8:00–20:00 + дыхание 4-8 (удлинённый выдох) 2 минуты.",
    "Манипуляция в разговоре": "Протокол: Тайм-аут 2 минуты, квадратное дыхание (4-4-4-4), затем серый камень.",
    "Прокрастинация": "Протокол: Огненное дыхание (капалабхати) 1 минута, затем 5 минут работы по таймеру.",
    "Новостная тревога": "Протокол: Концентрация на звуке 3 минуты + дыхание 4-8 перед входом в новости.",
    "Конфликт с коллегой": "Протокол: Выдох длиннее вдоха (4-8), 5 циклов, затем 'Я подумаю'."
}

BREATHING_PRACTICES = {
    "Квадратное дыхание (4-4-4-4)": "Вдох носом на 4 счёта → задержка 4 → выдох носом на 4 → задержка 4. Повтори 4-6 раз. Успокаивает и центрирует.",
    "Огненное дыхание (капалабхати)": "Ритмичные мощные выдохи через нос, живот толкает воздух. Вдохи пассивные. Начни с 30 выдохов, затем отдых. Даёт энергию.",
    "Удлинённый выдох (4-8)": "Вдох на 4 счёта, выдох на 8. Пауза после выдоха. Делай 2-3 минуты. Снижает тревогу и реактивность.",
    "Попеременное дыхание (нади шодхана)": "Закрой правую ноздрю, вдох левой → закрой левую, выдох правой → вдох правой → выдох левой. Балансирует полушария.",
    "Дыхание Вима Хофа (упрощённое)": "30 глубоких вдохов-выдохов без пауз, затем выдох до конца и задержка на максимум. Повтори 3 раунда. Бодрит и оксигенирует."
}

# --- Обработчики команд ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛡️ *Экосистема человека 2.0*\n\n"
        "Команды:\n"
        "/attack — выбрать угрозу и получить протокол\n"
        "/breathe — случайная дыхательная практика\n"
        "/help — помощь",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛡️ *Помощь*\n\n"
        "• /attack — протокол защиты от конкретной угрозы\n"
        "• /breathe — случайная дыхательная практика\n"
        "• /start — приветствие"
    )

async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(name, callback_data=f"threat_{name}")] for name in THREATS.keys()]
    await update.message.reply_text("Выберите угрозу:", reply_markup=InlineKeyboardMarkup(keyboard))

async def breathe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name, desc = random.choice(list(BREATHING_PRACTICES.items()))
    await update.message.reply_text(
        f"🌬️ *{name}*\n\n{desc}\n\n/attack — для защиты от угроз",
        parse_mode="Markdown"
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("threat_"):
        threat = data.replace("threat_", "")
        protocol = THREATS.get(threat, "Протокол не найден. Используйте /breathe.")
        await query.edit_message_text(
            f"🛡️ *{threat}*\n\n{protocol}\n\n/attack — другая угроза\n/breathe — дыхание",
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text("Неизвестная команда. Используйте /attack или /breathe")

# --- Асинхронный запуск с веб-хуком для Render ---
async def run_bot():
    # Создаём приложение бота без Updater (ручное управление)
    app = Application.builder().token(TOKEN).updater(None).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("attack", attack))
    app.add_handler(CommandHandler("breathe", breathe))
    app.add_handler(CallbackQueryHandler(handle_callback))

    # Устанавливаем веб-хук
    webhook_url = f"{WEBHOOK_URL}/telegram"
    await app.bot.set_webhook(url=webhook_url, allowed_updates=Update.ALL_TYPES)
    logger.info(f"Webhook установлен на {webhook_url}")

    # Создаём Starlette-приложение для обработки входящих запросов
    async def telegram_webhook(request: Request):
    logger.info("!!! WEBHOOK ВЫЗВАН !!!")
        try:
            data = await request.json()
            update = Update.de_json(data, app.bot)
            await app.update_queue.put(update)
        except Exception as e:
            logger.error(f"Ошибка webhook: {e}")
        return Response()

    async def health_check(request: Request):
        return PlainTextResponse("OK")

    starlette_app = Starlette(routes=[
    # Теперь Render найдет ваш бот по основному адресу
    Route("/", health_check, methods=["GET"]), 
    # Путь для вебхука Telegram
    Route("/telegram", telegram_webhook, methods=["POST"]),
])

   # Запускаем сервер, который будет держать порт открытым для Render
    import uvicorn
    config = uvicorn.Config(starlette_app, host="0.0.0.0", port=PORT,log_level="info")
    server = uvicorn.Server(config)
    
    try:
        await server.serve()
    finally:
        # Важно корректно остановить бота
        await app.stop()
        await app.shutdown()
    
    
if __name__ == "__main__":
    asyncio.run(run_bot())
