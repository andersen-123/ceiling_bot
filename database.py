import os
import sqlite3
from datetime import datetime


DB_PATH = os.path.join(os.path.dirname(__file__), 'expenses.db')


def get_db():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_db()
    c = conn.cursor()
    
    c.execute("""CREATE TABLE IF NOT EXISTS objects
        (id INTEGER PRIMARY KEY, user_id INTEGER, name TEXT, address TEXT, 
         area REAL, cost REAL, date TEXT)""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS expenses
        (id INTEGER PRIMARY KEY, user_id INTEGER, object_id INTEGER, 
         category TEXT, amount REAL, date TEXT)""")
    
    c.execute("""CREATE TABLE IF NOT EXISTS workers
        (id INTEGER PRIMARY KEY, user_id INTEGER, object_id INTEGER, 
         name TEXT, used_car INTEGER DEFAULT 0)""")
    
    conn.commit()
    conn.close()

# OBJECTS
def add_object(user_id, name, address, area, cost):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO objects (user_id, name, address, area, cost, date) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, name, address, area, cost, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def get_objects(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name, cost FROM objects WHERE user_id=? ORDER BY id DESC", (user_id,))
    objects = c.fetchall()
    conn.close()
    return objects

def get_object_by_id(user_id, object_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name, cost FROM objects WHERE user_id=? AND id=?", (user_id, object_id))
    obj = c.fetchone()
    conn.close()
    return obj

# EXPENSES
def add_expense(user_id, object_id, category, amount):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO expenses (user_id, object_id, category, amount, date) VALUES (?, ?, ?, ?, ?)",
        (user_id, object_id, category, amount, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def get_expenses(user_id, object_id):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "SELECT category, SUM(amount) as total FROM expenses WHERE user_id=? AND object_id=? GROUP BY category",
        (user_id, object_id)
    )
    expenses = c.fetchall()
    conn.close()
    return expenses

# WORKERS
def add_worker(user_id, object_id, name, used_car=0):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO workers (user_id, object_id, name, used_car) VALUES (?, ?, ?, ?)",
        (user_id, object_id, name, used_car)
    )
    conn.commit()
    conn.close()

def get_workers(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        """SELECT DISTINCT name FROM workers WHERE user_id=? ORDER BY name""",
        (user_id,)
    )
    workers = c.fetchall()
    conn.close()
    return [(name[0],) for name in workers]

def worker_exists(user_id, name):
    """Проверить существует ли монтажник с таким именем"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM workers WHERE user_id=? AND name=?", (user_id, name))
    exists = c.fetchone() is not None
    conn.close()
    return exists


def get_worker_objects(user_id, worker_id):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        """SELECT DISTINCT o.id, o.name, o.cost FROM workers w
           JOIN objects o ON w.object_id = o.id
           WHERE w.user_id=? AND w.id=? ORDER BY o.name""",
        (user_id, worker_id)
    )
    objects = c.fetchall()
    conn.close()
    return objects

def get_object_workers(user_id, object_id):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "SELECT id, name, used_car FROM workers WHERE user_id=? AND object_id=?",
        (user_id, object_id)
    )
    workers = c.fetchall()
    conn.close()
    return workers

# SALARY CALCULATION
def calculate_object_salary(user_id, object_id):
    """
    Формула расчёта зарплаты:
    1. Остаток = Стоимость - Материалы - Бензин
    2. Амортизация (5%) = 5% от остатка
    3. Базовая зарплата = (Остаток - Амортизация) / кол-во монтажников
    4. Добавить амортизацию тому, кто на авто
    5. Возместить бензин тому, кто потратил
    """
    conn = get_db()
    c = conn.cursor()
    
    # Получить объект
    c.execute("SELECT cost FROM objects WHERE user_id=? AND id=?", (user_id, object_id))
    obj = c.fetchone()
    if not obj:
        conn.close()
        return None
    
    total_cost = obj[0]
    
    # Получить расходы
    c.execute(
        "SELECT category, SUM(amount) FROM expenses WHERE user_id=? AND object_id=? GROUP BY category",
        (user_id, object_id)
    )
    expenses = c.fetchall()
    
    materials = 0
    fuel = 0
    for category, amount in expenses:
        if category == 'materials':
            materials = amount
        elif category == 'fuel':
            fuel = amount
    
    # Получить монтажников
    c.execute(
        "SELECT name, used_car FROM workers WHERE user_id=? AND object_id=?",
        (user_id, object_id)
    )
    workers = c.fetchall()
    
    conn.close()
    
    if not workers:
        return None
    
    # Расчёты
    remainder = total_cost - materials - fuel
    depreciation = remainder * 0.05
    salary_without_depreciation = (remainder - depreciation) / len(workers)
    
    salaries = {}
    for worker_name, used_car in workers:
        salary = salary_without_depreciation
        
        # Добавить амортизацию если использовал авто
        if used_car:
            salary += depreciation
        
        # Возместить бензин
        fuel_share = fuel / len(workers) if fuel > 0 else 0
        salary += fuel_share
        
        salaries[worker_name] = {
            'base': salary_without_depreciation,
            'fuel_share': fuel_share,
            'depreciation': depreciation if used_car else 0,
            'total': salary
        }
    
    return {
        'total_cost': total_cost,
        'materials': materials,
        'fuel': fuel,
        'remainder': remainder,
        'depreciation': depreciation,
        'salaries': salaries,
        'workers_count': len(workers)
    }

def set_worker_used_car(user_id, object_id, worker_name, used_car):
    """Установить что монтажник использовал авто на объекте"""
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "UPDATE workers SET used_car=? WHERE user_id=? AND object_id=? AND name=?",
        (used_car, user_id, object_id, worker_name)
    )
    conn.commit()
    conn.close()


def get_all_salaries(user_id):
    """Получить расчёты зарплаты по всем объектам"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM objects WHERE user_id=?", (user_id,))
    objects = c.fetchall()
    conn.close()
    
    all_salaries = {}
    for obj_id, in objects:
        obj_name = get_object_by_id(user_id, obj_id)
        if obj_name:
            all_salaries[obj_name[1]] = calculate_object_salary(user_id, obj_id)
    
    return all_salaries
