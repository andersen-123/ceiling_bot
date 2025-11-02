from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_objects, add_expense
from handlers.menu import cancel_button, main_keyboard

async def show_expenses_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    objects = get_objects(update.effective_user.id)
    
    text = "💰 <b>ДОБАВИТЬ РАСХОД</b>\n\n"
    keyboard = []
    
    if not objects:
        text += "⚠️ Нет объектов. Сначала добавьте объект!"
        keyboard.append([InlineKeyboardButton("🏠 Меню", callback_data="back_main")])
    else:
        text += "Выберите объект:"
        for obj_id, name in [(o[0], o[1]) for o in objects]:
            keyboard.append([InlineKeyboardButton(f"📋 {name}", callback_data=f"expense_obj_{obj_id}")])
        keyboard.append([InlineKeyboardButton("🏠 Меню", callback_data="back_main")])
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    return 6

async def select_expense_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    obj_id = query.data.split('_')[2]
    context.user_data['expense_object_id'] = int(obj_id)
    
    keyboard = [
        [InlineKeyboardButton("🛠️ Материалы", callback_data="cat_materials")],
        [InlineKeyboardButton("⛽ Бензин", callback_data="cat_fuel")],
        [InlineKeyboardButton("💼 Прочие", callback_data="cat_other")],
        [InlineKeyboardButton("🏠 Меню", callback_data="back_main")]
    ]
    
    await query.edit_message_text(
        "💰 <b>Выберите категорию:</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return 8

async def enter_expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    category = query.data.split('_')[1]
    context.user_data['expense_category'] = category
    
    await query.edit_message_text(
        "💵 <b>Введите сумму (в ₽):</b>",
        reply_markup=cancel_button(),
        parse_mode="HTML"
    )
    return 9

async def save_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text)
    except:
        await update.message.reply_text(
            "❌ Введите число (например: 5000):",
            reply_markup=cancel_button()
        )
        return 9
    
    add_expense(
        update.effective_user.id,
        context.user_data['expense_object_id'],
        context.user_data['expense_category'],
        amount
    )
    
    await update.message.reply_text(
        "✅ Расход добавлен!\n\n🏠 Главное меню:",
        reply_markup=main_keyboard()
    )
    return 0
