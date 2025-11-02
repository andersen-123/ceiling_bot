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
    
    add_worker(
        update.effective_user.id,
        obj_id,
        context.user_data['worker_name']
    )
    
    await query.edit_message_text(
        f"✅ Монтажник '{context.user_data['worker_name']}' добавлен!\n\n🏠 Главное меню:",
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

