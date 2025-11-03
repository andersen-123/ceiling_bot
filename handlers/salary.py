from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_all_salaries, get_objects
from handlers.menu import main_keyboard

async def show_salary_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    objects = get_objects(update.effective_user.id)
    
    text = "💵 <b>РАСЧЁТ ЗАРПЛАТЫ</b>\n\n"
    
    if not objects:
        text += "Нет объектов для расчёта"
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="back_main")]]),
            parse_mode="HTML"
        )
        return 14
    
    all_salaries = get_all_salaries(update.effective_user.id)
    
    for obj_name, salary_data in all_salaries.items():
        if not salary_data:
            continue
        
        text += f"📋 <b>{obj_name}</b>\n"
        text += f"   💰 Стоимость объекта: {salary_data['total_cost']}₽\n"
        text += f"   - Всего расходов: {salary_data['total_expenses']}₽\n"
        text += f"   = Остаток: {salary_data['remainder']}₽\n"
        text += f"   - Амортизация авто (5%): {salary_data['depreciation_total']}₽\n"
        text += f"   📊 Монтажников: {salary_data['workers_count']}\n\n"
        
        text += "   <b>🧑‍💼 Зарплата:</b>\n"
        for worker_name, salary_info in salary_data['salaries'].items():
            text += f"      👤 {worker_name}:\n"
            text += f"         💵 Базовая: {salary_info['base']:.0f}₽\n"
            if salary_info['depreciation'] > 0:
                text += f"         🚗 Амортизация: +{salary_info['depreciation']:.0f}₽\n"
            text += f"         <b>✅ ИТОГО: {salary_info['total']:.0f}₽</b>\n"
        text += "\n"
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="back_main")]]),
        parse_mode="HTML"
    )
    return 14

