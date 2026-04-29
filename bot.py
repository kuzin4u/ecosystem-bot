import os
import random
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Токен из переменной окружения
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("Переменная TELEGRAM_BOT_TOKEN не установлена")

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ваши данные (угрозы и практики)
THREATS = {
    "Соцсети (залипание)": "Протокол: Блокировка приложений 8:00–20:00 + дыхание 4-8 (удлинённый выдох) 2 минуты.",
    "Манипуляция в разговоре": "Протокол: Тайм-аут 2 минуты, квадратное дыхание (4-4-4-4), затем серый камень.",
    "Прокрастинация": "Протокол: Огненное дыхание (капалабхати) 1 минута, затем 5 минут работы по таймеру.",
    "Новостная тревога": "Протокол: Концентрация на звуке 3 минуты + дыхание 4-8 перед входом в новости.",
    "Конфликт с коллегой": "Протокол: Выдох длиннее вдоха (4-8), 5 циклов, затем 'Я подумаю'."
}

BREATHING_PRACTICES = {
    "Квадратное дыхание (4-4-4-4)": "Вдох носом на 4 счёта → задержка 4 → выдох носом на 4 → задержка 4. Повтори 4-6 раз. Успокаивает.",
    "Огненное дыхание (капалабхати)": "Ритмичные мощные выдохи через нос. Начни с 30 выдохов. Даёт энергию.",
    "Удлинённый выдох (4-8)": "Вдох на 4 счёта, выдох на 8. Делай 2-3 минуты. Снижает тревогу.",
    "Попеременное дыхание (нади шодхана)": "Закрой правую ноздрю, вдох левой → закрой левую, выдох правой. Балансирует полушария.",
    "Дыхание Вима Хофа (упрощённое)": "30 глубоких вдохов-выдохов, затем задержка после выдоха. Бодрит."
}

# Обработчики команд
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛡️ *Экосистема человека 2.0*\n\n"
        "/attack — выбрать угрозу\n"
        "/breathe — случайная дыхательная практика\n"
        "/help — помощь",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛡️ *Помощь*\n\n"
        "/attack — протокол защиты\n"
        "/breathe — дыхательная практика\n"
        "/start — приветствие"
    )

async def attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(name, callback_data=f"threat_{name}")] for name in THREATS.keys()]
    await update.message.reply_text("Выберите угрозу:", reply_markup=InlineKeyboardMarkup(keyboard))

async def breathe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name, desc = random.choice(list(BREATHING_PRACTICES.items()))
    await update.message.reply_text(
        f"🌬️ *{name}*\n\n{desc}\n\n/attack — для защиты",
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

# Запуск в режиме polling
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("attack", attack))
    app.add_handler(CommandHandler("breathe", breathe))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    logger.info("Бот запущен в режиме polling")
    app.run_polling()

if __name__ == "__main__":
    main()

