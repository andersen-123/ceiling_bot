import os
import logging
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters, ContextTypes
from telegram import Update

# Импорты обработчиков
from handlers.menu import handle_menu, cancel_action, back_to_main, start
from handlers.objects import add_object_step1, add_object_step2, add_object_step3, add_object_step4, add_object_save, show_objects
from handlers.expenses import show_expenses_menu, select_expense_category, enter_expense_amount, save_expense
from handlers.workers import show_workers_menu, add_worker_step1, add_worker_step2, add_worker_save, list_workers
from handlers.salary import show_salary_menu

from database import init_db

load_dotenv()
logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN') or '5326573614:AAGjV2gUnb5WPaL_3637dmyMoZmjhfRbc2I'


# States
MAIN_MENU = 0
OBJECTS_MENU = 1
ADD_OBJECT_NAME = 2
ADD_OBJECT_ADDRESS = 3
ADD_OBJECT_AREA = 4
ADD_OBJECT_COST = 5
EXPENSES_MENU = 6
SELECT_EXPENSE_OBJECT = 7
SELECT_EXPENSE_CATEGORY = 8
ENTER_EXPENSE_AMOUNT = 9
WORKERS_MENU = 10
REPORTS_MENU = 11
ADD_WORKER_NAME = 12
ADD_WORKER_OBJECT = 13
SALARY_MENU = 14

def main():
    init_db()
    app = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MAIN_MENU: [
                CommandHandler('start', start),
                CallbackQueryHandler(handle_menu, pattern="^menu_"),
                CallbackQueryHandler(back_to_main, pattern="^back_main$"),
            ],
            OBJECTS_MENU: [
                CommandHandler('start', start),
                CallbackQueryHandler(add_object_step1, pattern="^add_object$"),
                CallbackQueryHandler(show_objects, pattern="^show_objects$"),
                CallbackQueryHandler(back_to_main, pattern="^back_main$"),
            ],
            ADD_OBJECT_NAME: [
                CommandHandler('start', start),
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_object_step2),
                CallbackQueryHandler(cancel_action, pattern="^cancel_action$"),
            ],
            ADD_OBJECT_ADDRESS: [
                CommandHandler('start', start),
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_object_step3),
                CallbackQueryHandler(cancel_action, pattern="^cancel_action$"),
            ],
            ADD_OBJECT_AREA: [
                CommandHandler('start', start),
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_object_step4),
                CallbackQueryHandler(cancel_action, pattern="^cancel_action$"),
            ],
            ADD_OBJECT_COST: [
                CommandHandler('start', start),
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_object_save),
                CallbackQueryHandler(cancel_action, pattern="^cancel_action$"),
            ],
            EXPENSES_MENU: [
                CommandHandler('start', start),
                CallbackQueryHandler(select_expense_category, pattern="^expense_obj_"),
                CallbackQueryHandler(back_to_main, pattern="^back_main$"),
            ],
            SELECT_EXPENSE_CATEGORY: [
                CommandHandler('start', start),
                CallbackQueryHandler(enter_expense_amount, pattern="^cat_"),
                CallbackQueryHandler(back_to_main, pattern="^back_main$"),
            ],
            ENTER_EXPENSE_AMOUNT: [
                CommandHandler('start', start),
                MessageHandler(filters.TEXT & ~filters.COMMAND, save_expense),
                CallbackQueryHandler(cancel_action, pattern="^cancel_action$"),
            ],
            WORKERS_MENU: [
                CommandHandler('start', start),
                CallbackQueryHandler(add_worker_step1, pattern="^add_worker$"),
                CallbackQueryHandler(list_workers, pattern="^list_workers$"),
                CallbackQueryHandler(back_to_main, pattern="^back_main$"),
            ],
            ADD_WORKER_NAME: [
                CommandHandler('start', start),
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_worker_step2),
                CallbackQueryHandler(cancel_action, pattern="^cancel_action$"),
            ],
            ADD_WORKER_OBJECT: [
                CommandHandler('start', start),
                CallbackQueryHandler(add_worker_save, pattern="^worker_obj_"),
                CallbackQueryHandler(back_to_main, pattern="^back_main$"),
            ],

            SALARY_MENU: [
                CommandHandler('start', start),
                CallbackQueryHandler(back_to_main, pattern="^back_main$"),
            ],
            REPORTS_MENU: [
                CommandHandler('start', start),
                CallbackQueryHandler(back_to_main, pattern="^back_main$"),
            ],
        },
        fallbacks=[
            CommandHandler('start', start),
        ],
    )
    
    app.add_handler(conv_handler)
    print("✅ Бот запущен!")
    app.run_polling()

if __name__ == '__main__':
    main()
