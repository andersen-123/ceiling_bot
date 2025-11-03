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
    Правильный расчёт зарплаты:
    1. Остаток = 100% (Стоимость объекта) - Расходы (материалы, бензин, прочие)
    2. Амортизация авто = 5% от остатка (только для тех кто использует авто)
    3. Зарплата после амортизации = Остаток - Амортизация = делится на количество монтажников
    4. Каждый получает: базовую часть + возмещение бензина (если потратил)
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
    expenses_list = c.fetchall()
    
    total_expenses = sum(amount for _, amount in expenses_list)
    
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
    remainder = total_cost - total_expenses  # 100% - расходы
    
    # Амортизация = 5% от остатка, но начисляется ТОЛЬКО тем кто на авто
    workers_with_car = sum(1 for _, used_car in workers if used_car)
    depreciation_per_car = (remainder * 0.05) if workers_with_car > 0 else 0
    
    # Зарплата после амортизации
    salary_pool = remainder - (depreciation_per_car * workers_with_car)
    base_salary = salary_pool / len(workers)
    
    salaries = {}
    for worker_name, used_car in workers:
        salary = base_salary
        
        # Добавить амортизацию если использовал авто
        if used_car:
            salary += depreciation_per_car
        
        salaries[worker_name] = {
            'base': base_salary,
            'depreciation': depreciation_per_car if used_car else 0,
            'total': salary
        }
    
    return {
        'total_cost': total_cost,
        'total_expenses': total_expenses,
        'remainder': remainder,
        'depreciation_total': depreciation_per_car * workers_with_car,
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
