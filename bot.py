from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import requests
import json
from decouple import config  # Для чтения переменных окружения


# Команда /start
async def start(update: Update, context):
    # Создаем клавиатуру с кнопкой "Меню"
    menu_button = [[KeyboardButton("Меню")]]
    reply_markup = ReplyKeyboardMarkup(menu_button, resize_keyboard=True)
    await update.message.reply_text("Добро пожаловать! Нажмите 'Меню' для выбора действия.", reply_markup=reply_markup)


# Обработка нажатия на кнопку "Меню"
async def handle_menu(update: Update, context):
    # Создаем клавиатуру с кнопками "Добавить расход" и "Потрачено в этом месяце"
    menu_buttons = [
        [KeyboardButton("Добавить расход")],
        [KeyboardButton("Потрачено в этом месяце")]
    ]
    reply_markup = ReplyKeyboardMarkup(menu_buttons, resize_keyboard=True)
    await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)


# Обработка нажатия на кнопку "Добавить расход"
async def handle_add_expense(update: Update, context):
    # Показываем кнопки с категориями и кнопкой "Назад"
    categories = [
        "Продукты", "Коммунальные", "Гулянки",
        "Аптеки", "Авто", "Одежда", "Прочее"
    ]
    category_buttons = [[KeyboardButton(cat)] for cat in categories]
    category_buttons.append([KeyboardButton("Назад")])  # Добавляем кнопку "Назад"
    reply_markup = ReplyKeyboardMarkup(category_buttons, resize_keyboard=True)
    await update.message.reply_text("Выберите категорию:", reply_markup=reply_markup)


# Обработка выбора категории
async def handle_category_selection(update: Update, context):
    category = update.message.text
    if category == "Назад":
        # Возвращаемся в главное меню
        await handle_menu(update, context)
    else:
        context.user_data['category'] = category
        await update.message.reply_text(f"Вы выбрали категорию: {category}. Введите сумму:")


# Обработка ввода суммы
async def handle_amount_input(update: Update, context):
    if 'category' in context.user_data:
        try:
            amount = float(update.message.text)
            category = context.user_data['category']

            # Отправляем данные в Django-бэкенд
            data = {
                'category': category,
                'amount': amount
            }
            response = requests.post(
                'http://127.0.0.1:8000/finance/expense/',
                data=json.dumps(data),
                headers={'Content-Type': 'application/json'}
            )
            if response.status_code == 200:
                await update.message.reply_text(f"Добавлено {amount} руб. в категорию '{category}'.")
            else:
                await update.message.reply_text("Ошибка при добавлении расхода. Попробуйте позже.")
        except ValueError:
            await update.message.reply_text("Сумма должна быть числом. Попробуйте снова.")
        finally:
            # Очищаем выбранную категорию
            context.user_data.pop('category', None)
    else:
        await update.message.reply_text("Используйте кнопки для взаимодействия с ботом.")


# Обработка нажатия на кнопку "Потрачено в этом месяце"
async def handle_show_total(update: Update, context):
    try:
        response = requests.get('http://127.0.0.1:8000/finance/expense/')
        if response.status_code == 200:
            data = response.json()
            total = data.get('total_expenses', 0)
            category_expenses = data.get('category_expenses', {})

            # Формируем сообщение с общей суммой и расходами по категориям
            message = f"Суммарные расходы за текущий месяц: {total} руб.\n\n"
            message += "Расходы по категориям:\n"
            for category, amount in category_expenses.items():
                message += f"{category}: {amount} руб.\n"

            await update.message.reply_text(message)
        else:
            await update.message.reply_text("Ошибка при получении данных. Попробуйте позже.")
    except Exception as e:
        await update.message.reply_text(f"Произошла ошибка: {e}")


# Основная функция для запуска бота
def main():
    # Чтение токена из переменной окружения
    token = config('TELEGRAM_BOT_TOKEN')

    # Создаем Application
    application = Application.builder().token(token).build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Text("Меню"), handle_menu))
    application.add_handler(MessageHandler(filters.Text("Добавить расход"), handle_add_expense))
    application.add_handler(MessageHandler(filters.Text("Потрачено в этом месяце"), handle_show_total))
    application.add_handler(MessageHandler(filters.Text([
        "Продукты", "Коммунальные", "Гулянки",
        "Аптеки", "Авто", "Одежда", "Прочее", "Назад"
    ]), handle_category_selection))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount_input))

    # Запускаем бота
    print("Бот запущен...")
    application.run_polling()


if __name__ == '__main__':
    main()
