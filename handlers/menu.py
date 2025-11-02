from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import init_db

def main_keyboard():
    keyboard = [
        [InlineKeyboardButton("🏠 Объекты", callback_data="menu_objects")],
        [InlineKeyboardButton("💰 Расходы", callback_data="menu_expenses")],
        [InlineKeyboardButton("👥 Монтажники", callback_data="menu_workers")],
        [InlineKeyboardButton("💵 Зарплата", callback_data="menu_salary")],
        [InlineKeyboardButton("📊 Отчёты", callback_data="menu_reports")],
    ]
    return InlineKeyboardMarkup(keyboard)

def cancel_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ Отмена", callback_data="cancel_action")]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_db()
    if update.message:
        await update.message.reply_text(
            "🏠 <b>ГЛАВНОЕ МЕНЮ</b>\n\nВыберите действие:",
            reply_markup=main_keyboard(),
            parse_mode="HTML"
        )
    else:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "🏠 <b>ГЛАВНОЕ МЕНЮ</b>\n\nВыберите действие:",
            reply_markup=main_keyboard(),
            parse_mode="HTML"
        )
    return 0

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Импорты для избежания циклических зависимостей
    from handlers.objects import show_objects
    from handlers.expenses import show_expenses_menu
    from handlers.workers import show_workers_menu
    from handlers.salary import show_salary_menu
    
    if query.data == "menu_objects":
        return await show_objects(update, context)
    elif query.data == "menu_expenses":
        return await show_expenses_menu(update, context)
    elif query.data == "menu_workers":
        return await show_workers_menu(update, context)
    elif query.data == "menu_salary":
        return await show_salary_menu(update, context)
    elif query.data == "menu_reports":
        await query.edit_message_text(
            "📊 <b>ОТЧЁТЫ</b>\n\n(В разработке)",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="back_main")]]),
            parse_mode="HTML"
        )
        return 11
    
    return 0

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🏠 <b>ГЛАВНОЕ МЕНЮ</b>\n\nВыберите действие:",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )
    return 0

async def cancel_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🏠 <b>ГЛАВНОЕ МЕНЮ</b>\n\nВыберите действие:",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )
    return 0

