from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext, JobQueue
import sqlite3
from datetime import datetime, time

# Telegram Bot Token
TOKEN = "7429779028:AAHsO1eKLL7-m-vhzf8m-i3bBX1kaheo7Io"

# Database connection
DB_PATH = "db/finance.db"

def execute_query(query, params=()):
    """Execute a query in the SQLite database."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.fetchall()

# Start command with buttons
async def start(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    username = update.message.chat.username

    user = execute_query("SELECT * FROM users WHERE chat_id = ?", (user_id,))
    if not user:
        execute_query("INSERT INTO users (username, chat_id) VALUES (?, ?)", (username, user_id))
        await update.message.reply_text("Привет! Добро пожаловать в бота для управления финансами.")
    else:
        await update.message.reply_text("Вы уже зарегистрированы.")

    # Добавляем кнопки для выбора действия
    inline_keyboard = [
        [InlineKeyboardButton("Добавить расход", callback_data="add_expense")],
        [InlineKeyboardButton("Статистика", callback_data="view_stats")],
        [InlineKeyboardButton("Установить бюджет", callback_data="set_budget")],
    ]
    reply_markup_inline = InlineKeyboardMarkup(inline_keyboard)

    # Добавляем кнопки, которые будут видны внизу экрана постоянно
    reply_keyboard = [
        ["Добавить расход", "Статистика"],
        ["Бюджет", "Помощь"],
        ["Обнулить все"]
    ]
    reply_markup_reply = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

    await update.message.reply_text("Что вы хотите сделать?", reply_markup=reply_markup_inline)
    await update.message.reply_text("Используйте клавиши внизу для быстрого доступа к командам:", reply_markup=reply_markup_reply)

# Handle button clicks
async def handle_button_click(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    if query.data == "add_expense":
        await query.message.reply_text(
            "💸 *Введите расход в формате:* `<категория> <сумма>`\n\n"
            "Например: `Еда 500` или `Транспорт 150`.",
            parse_mode="Markdown"
        )
        context.user_data["action"] = "add_expense"
    elif query.data == "view_stats":
        # Передаем Update в функцию stats
        await stats(update, context)
    elif query.data == "set_budget":
        await query.message.reply_text(
            "💰 *Введите сумму бюджета на месяц:* \n\n"
            "Например: `50000`",
            parse_mode="Markdown"
        )
        context.user_data["action"] = "set_budget"

# Add expense, set budget, or reset expenses based on user input
async def handle_message(update: Update, context: CallbackContext):
    text = update.message.text.lower()

    if text == "помощь":
        await help_command(update, context)
        return
    elif text == "добавить расход":
        await update.message.reply_text(
            "💸 *Введите расход в формате:* `<категория> <сумма>`\n\n"
            "Например: `Еда 500` или `Транспорт 150`.",
            parse_mode="Markdown"
        )
        context.user_data["action"] = "add_expense"
        return
    elif text == "статистика":
        await stats(update, context)
        return
    elif text == "бюджет":
        await update.message.reply_text(
            "💰 *Введите сумму бюджета на месяц:* \n\n"
            "Например: `50000`",
            parse_mode="Markdown"
        )
        context.user_data["action"] = "set_budget"
        return
    elif text == "обнулить все":
        # Подтверждение перед очисткой всех данных
        context.user_data["action"] = "reset_expenses"
        await update.message.reply_text(
            "⚠️ *Вы уверены, что хотите обнулить все расходы?* ⚠️\n\n"
            "Введите 'да', чтобы подтвердить, или любую другую команду, чтобы отменить.",
            parse_mode="Markdown"
        )
        return

    if "action" not in context.user_data:
        await update.message.reply_text("Выберите действие через кнопки.")
        return

    action = context.user_data["action"]

    if action == "add_expense":
        try:
            category, amount = update.message.text.split()
            amount = float(amount)

            user_id = update.message.chat_id
            execute_query(
                "INSERT INTO transactions (user_id, category, amount, date) VALUES ((SELECT id FROM users WHERE chat_id = ?), ?, ?, ?)",
                (user_id, category, amount, datetime.now())
            )
            # Улучшенное сообщение о добавлении расхода
            await update.message.reply_text(
                f"✅ *Добавлен расход!*\n\n"
                f"Категория: *{category.capitalize()}*\n"
                f"Сумма: *{amount}₽*\n\n"
                f"Спасибо за то, что добавили свои расходы! 💰",
                parse_mode="Markdown"
            )

        except ValueError:
            await update.message.reply_text("Ошибка: Введите данные в формате: <категория> <сумма>.")
        finally:
            context.user_data.pop("action", None)

    elif action == "set_budget":
        try:
            budget = float(update.message.text)
            user_id = update.message.chat_id

            execute_query(
                "INSERT OR REPLACE INTO budget (user_id, monthly_limit) VALUES ((SELECT id FROM users WHERE chat_id = ?), ?)",
                (user_id, budget)
            )
            await update.message.reply_text(
                f"🎯 *Месячный бюджет установлен!* \n\n"
                f"Бюджет: *{budget}₽*",
                parse_mode="Markdown"
            )
        except ValueError:
            await update.message.reply_text("Ошибка: Введите сумму бюджета числом.")
        finally:
            context.user_data.pop("action", None)

    elif action == "reset_expenses":
        if text == "да":
            user_id = update.message.chat_id
            execute_query("DELETE FROM transactions WHERE user_id = (SELECT id FROM users WHERE chat_id = ?)", (user_id,))
            await update.message.reply_text("🔄 *Все расходы были успешно обнулены!*", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ *Очистка отменена.*", parse_mode="Markdown")
        context.user_data.pop("action", None)

# View stats
async def stats(update: Update, context: CallbackContext):
    # Определяем, откуда пришел запрос: через CallbackQuery или команду
    if update.callback_query:
        user_id = update.callback_query.message.chat_id
        message = update.callback_query.message
    else:
        user_id = update.message.chat_id
        message = update.message

    # Выполняем запрос к базе данных для получения статистики расходов
    rows = execute_query(
        "SELECT category, SUM(amount) FROM transactions WHERE user_id = (SELECT id FROM users WHERE chat_id = ?) GROUP BY category",
        (user_id,)
    )

    if not rows:
        await message.reply_text("У вас ещё нет расходов.")
        return

    # Формируем сообщение со статистикой
    stats_message = "📊 *Статистика расходов:*\n\n"
    for category, total in rows:
        stats_message += f"- 🗂 *{category.capitalize()}:* {total}₽\n"

    # Добавление информации о прогрессе бюджета
    total_expenses = sum(row[1] for row in rows)
    budget = execute_query(
        "SELECT monthly_limit FROM budget WHERE user_id = (SELECT id FROM users WHERE chat_id = ?)",
        (user_id,)
    )
    budget = budget[0][0] if budget else None

    if budget :
        progress = (total_expenses / budget) * 100
        stats_message += (
            f"\n🎯 *Бюджет:* {budget}₽\n"
            f"💰 *Потрачено:* {total_expenses}₽\n"
            f"📈 *Статус использования бюджета:* {progress:.2f}%"
        )

    await message.reply_text(stats_message, parse_mode="Markdown")

# Command to manually reset expenses
async def reset_expenses(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    execute_query("DELETE FROM transactions WHERE user_id = (SELECT id FROM users WHERE chat_id = ?)", (user_id,))
    await update.message.reply_text("Ваши расходы были успешно обнулены.")

# Job to reset expenses at the beginning of every month
async def reset_expenses_job(context: CallbackContext):
    execute_query("DELETE FROM transactions WHERE date < date('now', 'start of month')")
    print("All expenses reset at the beginning of the month.")

# Help command
async def help_command(update: Update, context: CallbackContext):
    """Функция для команды /help."""
    keyboard = [
        [InlineKeyboardButton("Добавить расход", callback_data="add_expense")],
        [InlineKeyboardButton("Статистика", callback_data="view_stats")],
        [InlineKeyboardButton("Установить бюджет", callback_data="set_budget")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Выберите действие, используя кнопки ниже. Вот что я могу сделать:\n\n"
        "1️⃣ Добавить расход\n"
        "2️⃣ Просмотреть статистику\n"
        "3️⃣ Установить месячный бюджет\n\n"
        "Нажмите на соответствующую кнопку ниже ⬇️",
        reply_markup=reply_markup
    )

# Main function
def main():
    application = Application.builder().token(TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("reset_expenses", reset_expenses))

    # Callback query handler for inline buttons
    application.add_handler(CallbackQueryHandler(handle_button_click))

    # General message handler for actions (e.g., add expense, set budget, help command)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Job queue for resetting expenses monthly
    job_queue = application.job_queue
    job_queue.run_monthly(reset_expenses_job, when=time(hour=0, minute=0), day=1)

    # Start polling
    application.run_polling()

if __name__ == "__main__":
    main()
