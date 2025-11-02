from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_objects, add_object
from handlers.menu import cancel_button

async def show_objects(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    objects = get_objects(update.effective_user.id)
    
    text = "📋 <b>МОИ ОБЪЕКТЫ</b>\n\n"
    keyboard = []
    
    if objects:
        for obj_id, name, cost in objects:
            text += f"• {name} ({cost}₽)\n"
    else:
        text += "У вас нет объектов\n"
    
    keyboard.append([InlineKeyboardButton("➕ Добавить", callback_data="add_object")])
    keyboard.append([InlineKeyboardButton("🏠 Меню", callback_data="back_main")])
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="HTML")
    return 1

async def add_object_step1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📝 Введите название объекта:",
        reply_markup=cancel_button()
    )
    return 2

async def add_object_step2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['object_name'] = update.message.text
    await update.message.reply_text(
        "📍 Укажите адрес (или напишите '-' для пропуска):",
        reply_markup=cancel_button()
    )
    return 3

async def add_object_step3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['address'] = update.message.text if update.message.text != '-' else 'нет адреса'
    await update.message.reply_text(
        "📐 Укажите площадь в м² (или '-' для пропуска):",
        reply_markup=cancel_button()
    )
    return 4

async def add_object_step4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.message.text == '-':
            context.user_data['area'] = None
        else:
            context.user_data['area'] = float(update.message.text)
    except:
        await update.message.reply_text(
            "❌ Введите число (например: 25 или 25.5):",
            reply_markup=cancel_button()
        )
        return 4
    
    await update.message.reply_text(
        "💰 Укажите стоимость объекта (в ₽):",
        reply_markup=cancel_button()
    )
    return 5

async def add_object_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        cost = float(update.message.text)
    except:
        await update.message.reply_text(
            "❌ Введите число (например: 350000):",
            reply_markup=cancel_button()
        )
        return 5
    
    add_object(
        update.effective_user.id,
        context.user_data['object_name'],
        context.user_data.get('address', 'нет адреса'),
        context.user_data.get('area'),
        cost
    )
    
    from handlers.menu import main_keyboard
    await update.message.reply_text(
        "✅ Объект добавлен!\n\n🏠 Главное меню:",
        reply_markup=main_keyboard()
    )
    return 0
