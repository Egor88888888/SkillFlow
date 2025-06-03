import sqlite3
import re
from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Замените на ваш реальный Telegram ID и токен бота
ADMIN_ID = 6922033571
BOT_TOKEN = "7947398382:AAGYlrBiLsgKFCyFUsqRAfzWhOi8qORLQi8"

# Подключение к базе данных
conn = sqlite3.connect("skillflow.db", check_same_thread=False)
cursor = conn.cursor()

# Создание таблиц, если их нет
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    full_name TEXT,
    skills TEXT,
    phone TEXT,
    email TEXT,
    balance INTEGER DEFAULT 2
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS services (
    service_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    category TEXT,
    description TEXT,
    cost INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER,
    recipient_id INTEGER,
    amount INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# Главное меню
def main_menu_keyboard(is_admin=False):
    if is_admin:
        keyboard = [
            [KeyboardButton("📊 Статистика"), KeyboardButton("🔧 Управление комиссиями")],
            [KeyboardButton("💼 Управление премиум"), KeyboardButton("📋 Управление услугами")],
            [KeyboardButton("💰 Лог сделок"), KeyboardButton("ℹ️ О проекте")]
        ]
    else:
        keyboard = [
            [KeyboardButton("👤 Моя карточка"), KeyboardButton("➕ Добавить услугу")],
            [KeyboardButton("📋 Просмотреть услуги"), KeyboardButton("🔄 Передать Flow-часы")],
            [KeyboardButton("💰 Проверить баланс"), KeyboardButton("ℹ️ О проекте")]
        ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Проверка регистрации пользователя
def is_registered(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    return cursor.fetchone() is not None

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        await update.message.reply_text(
            "👋 Добро пожаловать в *SkillFlow* — административную панель!",
            reply_markup=main_menu_keyboard(is_admin=True)
        )
    elif is_registered(user_id):
        await update.message.reply_text(
            "👋 Рады видеть вас снова! Выберите действие из меню ниже:",
            reply_markup=main_menu_keyboard()
        )
    else:
        context.user_data["registration_step"] = "full_name"
        await update.message.reply_text(
            "✨ *Добро пожаловать в SkillFlow!* ✨\n\n"
            "SkillFlow — это революционная платформа, где *ваши навыки* становятся *вашей валютой*!\n\n"
            "🔹 *Что такое Flow-час?*\n"
            "Flow-час — это единица обмена на нашей платформе, эквивалентная одному часу вашего времени или стоимости вашей услуги.\n\n"
            "🌟 *Как это работает?*\n"
            "1️⃣ *Регистрируйтесь* и расскажите о своих навыках.\n"
            "2️⃣ *Добавляйте услуги* и устанавливайте их стоимость в Flow-часах.\n"
            "3️⃣ *Получайте Flow-часы*, оказывая услуги другим участникам.\n"
            "4️⃣ *Тратьте Flow-часы* на услуги, которые нужны вам!\n\n"
            "💡 *Пример:*\n"
            "Анна обучает английскому и устанавливает стоимость урока в *2 Flow-часа*. Иван нанимает Анну и оплачивает уроки своими Flow-часами. Затем Анна тратит заработанные Flow-часы на услуги дизайнера для создания своего сайта.\n\n"
            "🚀 *Готовы начать?* Пожалуйста, введите ваше полное имя для регистрации (например: Иван Иванов).",
            parse_mode=ParseMode.MARKDOWN
        )

# Обработчик процесса регистрации
async def handle_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.text.strip()
    step = context.user_data.get("registration_step")

    if step == "full_name":
        if len(message.split()) < 2:
            await update.message.reply_text("❌ Пожалуйста, введите ваше *полное имя* (например: Иван Иванов).", parse_mode=ParseMode.MARKDOWN)
            return
        context.user_data["full_name"] = message
        context.user_data["registration_step"] = "skills"
        await update.message.reply_text(
            f"🛠 Отлично, *{message}*! Теперь расскажите, какие навыки или услуги вы можете предложить? (например: Программирование, Дизайн)",
            parse_mode=ParseMode.MARKDOWN
        )
    elif step == "skills":
        if len(message) < 3:
            await update.message.reply_text("❌ Пожалуйста, укажите хотя бы один навык.")
            return
        context.user_data["skills"] = message
        context.user_data["registration_step"] = "phone"
        await update.message.reply_text("📞 Укажите ваш *номер телефона* для связи (например: +71234567890).", parse_mode=ParseMode.MARKDOWN)
    elif step == "phone":
        if not re.match(r"^\+\d{10,15}$", message):
            await update.message.reply_text("❌ Неверный формат номера. Пожалуйста, используйте формат +71234567890.")
            return
        context.user_data["phone"] = message
        context.user_data["registration_step"] = "email"
        await update.message.reply_text("✉️ Пожалуйста, укажите ваш *email* для связи (например: example@mail.com).", parse_mode=ParseMode.MARKDOWN)
    elif step == "email":
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", message):
            await update.message.reply_text("❌ Неверный формат email. Попробуйте снова.")
            return
        context.user_data["email"] = message

        # Сохранение пользователя в базе данных
        cursor.execute("""
        INSERT INTO users (user_id, username, full_name, skills, phone, email, balance)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            update.effective_user.username,
            context.user_data["full_name"],
            context.user_data["skills"],
            context.user_data["phone"],
            context.user_data["email"],
            2  # Начальный баланс
        ))
        conn.commit()
        context.user_data.clear()
        await update.message.reply_text(
            "🎉 *Регистрация завершена!* Теперь вы можете использовать все возможности SkillFlow.\n\nВаш стартовый баланс: *2 Flow-часа*.\n\nВыберите действие из меню ниже:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_menu_keyboard()
        )

# Обработчик профиля пользователя
async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cursor.execute("SELECT full_name, skills, phone, email, balance FROM users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()
    if user_data:
        await update.message.reply_text(
            f"👤 *Ваша карточка:*\n\n"
            f"**ФИО:** {user_data[0]}\n"
            f"**Навыки:** {user_data[1]}\n"
            f"**Телефон:** {user_data[2]}\n"
            f"**Email:** {user_data[3]}\n"
            f"**Баланс:** {user_data[4]} Flow-часов",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await update.message.reply_text("❌ Карточка не найдена.")

# Обработчик добавления услуги
async def add_service_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["add_service_step"] = "category"
    await update.message.reply_text("📂 *Добавление услуги*\n\nВведите *категорию* вашей услуги (например: 'Программирование', 'Дизайн').", parse_mode=ParseMode.MARKDOWN)

async def add_service_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("add_service_step")
    message = update.message.text.strip()
    user_id = update.effective_user.id

    if step == "category":
        context.user_data["category"] = message
        context.user_data["add_service_step"] = "description"
        await update.message.reply_text("📝 Пожалуйста, опишите вашу услугу. Что вы предлагаете? Какие задачи можете решить?", parse_mode=ParseMode.MARKDOWN)
    elif step == "description":
        context.user_data["description"] = message
        context.user_data["add_service_step"] = "cost"
        await update.message.reply_text(
            "💰 Установите *стоимость* вашей услуги в *Flow-часах*.\n\n*Что это значит?*\n"
            "Вы определяете, сколько Flow-часов стоит ваша услуга. 1 Flow-час равен одному часу вашего времени или эквиваленту стоимости вашей услуги.\n\n"
            "Например, если услуга занимает у вас 2 часа или вы оцениваете её в 2 часа работы, укажите стоимость *2 Flow-часа*.",
            parse_mode=ParseMode.MARKDOWN
        )
    elif step == "cost":
        try:
            cost = int(message)
            if cost <= 0:
                raise ValueError
            cursor.execute("""
            INSERT INTO services (user_id, category, description, cost)
            VALUES (?, ?, ?, ?)
            """, (
                user_id,
                context.user_data["category"],
                context.user_data["description"],
                cost
            ))
            conn.commit()
            context.user_data.pop("add_service_step", None)
            await update.message.reply_text("✅ *Услуга успешно добавлена!* Теперь другие пользователи могут её видеть и обращаться к вам.", parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu_keyboard())
        except ValueError:
            await update.message.reply_text("❌ Стоимость должна быть положительным числом. Попробуйте снова.")

# Обработчик просмотра услуг
async def view_services(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("""
    SELECT s.category, s.description, s.cost, u.full_name, u.user_id
    FROM services s
    JOIN users u ON s.user_id = u.user_id
    """)
    services = cursor.fetchall()
    if services:
        response = "📋 *Доступные услуги:*\n\n"
        for service in services:
            response += f"👤 **Исполнитель:** {service[3]} (ID: {service[4]})\n"
            response += f"📂 **Категория:** {service[0]}\n"
            response += f"📝 **Описание:** {service[1]}\n"
            response += f"💰 **Стоимость:** {service[2]} Flow-часов\n\n"
        await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text("❌ На данный момент нет доступных услуг.")

# Обработчик проверки баланса
async def check_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    balance = cursor.fetchone()
    if balance:
        await update.message.reply_text(f"💰 *Ваш текущий баланс:* {balance[0]} Flow-часов.", parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text("❌ Информация о балансе не найдена.")

# Обработчик перевода Flow-часов
async def transfer_flow_hours_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["transfer_step"] = "recipient_id"
    await update.message.reply_text("🔄 *Перевод Flow-часов*\n\nВведите *ID пользователя*, которому хотите перевести Flow-часы. Вы можете найти ID в его карточке или услуге.", parse_mode=ParseMode.MARKDOWN)

async def transfer_flow_hours_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("transfer_step")
    message = update.message.text.strip()
    user_id = update.effective_user.id

    if step == "recipient_id":
        try:
            recipient_id = int(message)
            if recipient_id == user_id:
                await update.message.reply_text("❌ Вы не можете перевести Flow-часы самому себе.")
                return
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (recipient_id,))
            if not cursor.fetchone():
                await update.message.reply_text("❌ Пользователь не найден. Пожалуйста, проверьте ID и попробуйте снова.")
                return
            context.user_data["recipient_id"] = recipient_id
            context.user_data["transfer_step"] = "amount"
            await update.message.reply_text("💸 Введите количество Flow-часов, которое хотите перевести.")
        except ValueError:
            await update.message.reply_text("❌ Неверный формат ID пользователя. Пожалуйста, введите числовое значение.")
    elif step == "amount":
        try:
            amount = int(message)
            if amount <= 0:
                raise ValueError
            cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
            sender_balance = cursor.fetchone()[0]
            if amount > sender_balance:
                await update.message.reply_text("❌ У вас недостаточно Flow-часов для совершения перевода.")
                return
            recipient_id = context.user_data["recipient_id"]
            # Обновление баланса
            cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, user_id))
            cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, recipient_id))
            # Запись транзакции
            cursor.execute("""
            INSERT INTO transactions (sender_id, recipient_id, amount)
            VALUES (?, ?, ?)
            """, (user_id, recipient_id, amount))
            conn.commit()
            context.user_data.pop("transfer_step", None)
            context.user_data.pop("recipient_id", None)
            await update.message.reply_text(f"✅ Вы успешно перевели {amount} Flow-часов пользователю с ID {recipient_id}!", reply_markup=main_menu_keyboard())
        except ValueError:
            await update.message.reply_text("❌ Сумма должна быть положительным числом.")

# Обработчик информации о проекте
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🌐 *О SkillFlow*\n\n"
        "SkillFlow — это инновационная платформа для обмена навыками и услугами без использования денег. "
        "Здесь вы можете предлагать свои услуги, зарабатывать Flow-часы и тратить их на услуги других участников.\n\n"
        "💡 *Как начать?*\n"
        "1️⃣ Добавьте свои услуги и установите их стоимость в Flow-часах.\n"
        "2️⃣ Просматривайте услуги других и обращайтесь к ним.\n"
        "3️⃣ Обменивайтесь Flow-часами и расширяйте свои возможности!",
        parse_mode=ParseMode.MARKDOWN
    )

# Обработчик административных команд
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ У вас нет доступа к этой функции.")
        return

    text = update.message.text.strip()

    if text == "📊 Статистика":
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM services")
        total_services = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM transactions")
        total_transactions = cursor.fetchone()[0]
        await update.message.reply_text(
            f"📊 *Статистика платформы:*\n\n"
            f"👥 *Всего пользователей:* {total_users}\n"
            f"🛠 *Всего услуг:* {total_services}\n"
            f"💸 *Всего транзакций:* {total_transactions}",
            parse_mode=ParseMode.MARKDOWN
        )
    elif text == "🔧 Управление комиссиями":
        await update.message.reply_text("⚙️ *Управление комиссиями* пока не реализовано.", reply_markup=main_menu_keyboard(is_admin=True))
    elif text == "💼 Управление премиум":
        await update.message.reply_text("💼 *Управление премиум-функциями* пока не реализовано.", reply_markup=main_menu_keyboard(is_admin=True))
    elif text == "📋 Управление услугами":
        await update.message.reply_text("🛠 *Управление услугами* пока не реализовано.", reply_markup=main_menu_keyboard(is_admin=True))
    elif text == "💰 Лог сделок":
        cursor.execute("""
        SELECT t.transaction_id, t.sender_id, t.recipient_id, t.amount, t.timestamp
        FROM transactions t
        ORDER BY t.timestamp DESC
        LIMIT 10
        """)
        transactions = cursor.fetchall()
        if transactions:
            response = "💰 *Последние транзакции:*\n\n"
            for tx in transactions:
                response += f"ID Транзакции: {tx[0]}\nОтправитель: {tx[1]}\nПолучатель: {tx[2]}\nСумма: {tx[3]} Flow-часов\nДата: {tx[4]}\n\n"
            await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text("❌ Транзакции не найдены.", reply_markup=main_menu_keyboard(is_admin=True))
    elif text == "ℹ️ О проекте":
        await about(update, context)
    else:
        await update.message.reply_text("❓ Неизвестная команда. Используйте кнопки меню.", reply_markup=main_menu_keyboard(is_admin=True))

# Обработчик текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    # Процесс регистрации
    if context.user_data.get("registration_step"):
        await handle_registration(update, context)
        return

    if user_id == ADMIN_ID:
        await admin_panel(update, context)
        return

    if is_registered(user_id):
        if text == "👤 Моя карточка":
            await show_profile(update, context)
        elif text == "➕ Добавить услугу":
            await add_service_start(update, context)
        elif text == "📋 Просмотреть услуги":
            await view_services(update, context)
        elif text == "💰 Проверить баланс":
            await check_balance(update, context)
        elif text == "🔄 Передать Flow-часы":
            await transfer_flow_hours_start(update, context)
        elif text == "ℹ️ О проекте":
            await about(update, context)
        elif context.user_data.get("add_service_step"):
            await add_service_process(update, context)
        elif context.user_data.get("transfer_step"):
            await transfer_flow_hours_process(update, context)
        else:
            await update.message.reply_text(
                "❓ Команда не распознана. Пожалуйста, используйте кнопки меню.",
                reply_markup=main_menu_keyboard()
            )
    else:
        await update.message.reply_text("❌ Вы не зарегистрированы. Пожалуйста, используйте /start для регистрации.")

# Основная функция
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == "__main__":
    main()
