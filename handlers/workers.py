from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_objects, get_workers, get_worker_objects, add_worker
from handlers.menu import cancel_button, main_keyboard

async def show_workers_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("➕ Добавить монтажника", callback_data="add_worker")],
        [InlineKeyboardButton("📋 Список монтажников", callback_data="list_workers")],
        [InlineKeyboardButton("🏠 Меню", callback_data="back_main")]
    ]
    
    await query.edit_message_text(
        "👥 <b>МОНТАЖНИКИ</b>",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )
    return 10

async def add_worker_step1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📝 Введите имя монтажника:",
        reply_markup=cancel_button()
    )
    return 12

async def add_worker_step2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from database import worker_exists
    
    worker_name = update.message.text.strip()
    
    # Проверка на уникальность
    if worker_exists(update.effective_user.id, worker_name):
        await update.message.reply_text(
            f"⚠️ Монтажник '{worker_name}' уже существует!",
            reply_markup=cancel_button()
        )
        return 12
    
    context.user_data['worker_name'] = worker_name
    
    objects = get_objects(update.effective_user.id)
    
    if not objects:
        await update.message.reply_text(
            "⚠️ Нет объектов! Сначала добавьте объект.",
            reply_markup=main_keyboard()
        )
        return 0
    
    text = "🏢 Выберите объект для монтажника:"
    keyboard = []
    for obj_id, name, _ in objects:
        keyboard.append([InlineKeyboardButton(f"📋 {name}", callback_data=f"worker_obj_{obj_id}")])
    keyboard.append([InlineKeyboardButton("🏠 Меню", callback_data="back_main")])
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return 13


async def add_worker_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    obj_id = int(query.data.split('_')[2])
    context.user_data['worker_object_id'] = obj_id
    
    # Спросить про авто
    keyboard = [
        [InlineKeyboardButton("🚗 Использует своё авто", callback_data="worker_car_yes")],
        [InlineKeyboardButton("❌ Нет своего авто", callback_data="worker_car_no")]
    ]
    
    await query.edit_message_text(
        f"👤 {context.user_data['worker_name']}\n\n🚗 Использует свой автомобиль на объектах?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return 14  # Новый state для выбора авто

async def worker_set_car(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    used_car = 1 if query.data == "worker_car_yes" else 0
    context.user_data['worker_used_car'] = used_car
    
    # Спросить про бензин
    keyboard = [
        [InlineKeyboardButton("⛽ Потратил на бензин", callback_data="worker_fuel_yes")],
        [InlineKeyboardButton("❌ Не потратил", callback_data="worker_fuel_no")]
    ]
    
    await query.edit_message_text(
        f"👤 {context.user_data['worker_name']}\n\n⛽ Потратил ли деньги на бензин?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return 15

async def worker_set_fuel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    spent_fuel = 1 if query.data == "worker_fuel_yes" else 0
    context.user_data['worker_spent_fuel'] = spent_fuel
    
    # Спросить про прочие траты
    keyboard = [
        [InlineKeyboardButton("💼 Были прочие траты", callback_data="worker_other_yes")],
        [InlineKeyboardButton("❌ Без прочих трат", callback_data="worker_other_no")]
    ]
    
    await query.edit_message_text(
        f"👤 {context.user_data['worker_name']}\n\n💼 Были ли другие личные траты на объект?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return 16


async def worker_save_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    other_expenses = 1 if query.data == "worker_other_yes" else 0
    context.user_data['worker_other_expenses'] = other_expenses
    
    from database import add_worker
    
    # Сохранить монтажника с флагом авто
    add_worker(
        update.effective_user.id,
        context.user_data['worker_object_id'],
        context.user_data['worker_name'],
        context.user_data['worker_used_car']
    )
    
    from handlers.menu import main_keyboard
    
    summary = f"✅ <b>Монтажник добавлен!</b>\n\n"
    summary += f"👤 {context.user_data['worker_name']}\n"
    summary += f"🚗 Авто: {'Да ✅' if context.user_data['worker_used_car'] else 'Нет ❌'}\n"
    summary += f"⛽ Бензин: {'Да ✅' if context.user_data['worker_spent_fuel'] else 'Нет ❌'}\n"
    summary += f"💼 Прочие траты: {'Да ✅' if context.user_data['worker_other_expenses'] else 'Нет ❌'}\n"
    
    await query.edit_message_text(
        summary + "\n\n🏠 Главное меню:",
        reply_markup=main_keyboard()
    )
    return 0


async def list_workers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    from database import get_db
    
    conn = get_db()
    c = conn.cursor()
    
    # Получить уникальных монтажников
    c.execute(
        """SELECT DISTINCT name FROM workers WHERE user_id=? ORDER BY name""",
        (update.effective_user.id,)
    )
    workers = c.fetchall()
    
    text = "👥 <b>СПИСОК МОНТАЖНИКОВ И ИХ ОБЪЕКТЫ</b>\n\n"
    
    if not workers:
        text += "Нет монтажников"
    else:
        for worker_row in workers:
            worker_name = worker_row[0]
            
            # Получить объекты этого монтажника
            c.execute(
                """SELECT DISTINCT o.name, o.cost FROM workers w
                   JOIN objects o ON w.object_id = o.id
                   WHERE w.user_id=? AND w.name=?
                   ORDER BY o.name""",
                (update.effective_user.id, worker_name)
            )
            objects = c.fetchall()
            
            total = sum(cost for _, cost in objects)
            
            text += f"👤 {worker_name}\n"
            text += f"   📊 Объектов: {len(objects)}\n"
            text += f"   💰 Общий заработок: {total}₽\n"
            
            for obj_name, obj_cost in objects:
                text += f"      🏢 {obj_name}: {obj_cost}₽\n"
            text += "\n"
    
    conn.close()
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Меню", callback_data="back_main")]]),
        parse_mode="HTML"
    )
    return 10

