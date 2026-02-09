# fix_database.py
import sqlite3
import os

# Путь к базе данных
db_path = 'db.sqlite3'

# Подключаемся к базе
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== 1. Структура таблицы users_customuser ===")
cursor.execute("PRAGMA table_info(users_customuser);")
columns = cursor.fetchall()
for col in columns:
    print(f"  {col[1]} ({col[2]})")

print("\n=== 2. Данные пользователей ===")
cursor.execute("SELECT id, username, country, country_id FROM users_customuser LIMIT 5;")
users = cursor.fetchall()
for user in users:
    print(f"  ID {user[0]}: {user[1]}, country='{user[2]}', country_id='{user[3]}'")

print("\n=== 3. Данные стран ===")
cursor.execute("SELECT id, code, name FROM users_country LIMIT 10;")
countries = cursor.fetchall()
for country in countries:
    print(f"  ID {country[0]}: {country[1]} - {country[2]}")

print("\n=== 4. Исправление данных ===")
# Очищаем поле country_id если оно содержит нечисловые значения
cursor.execute("""
    UPDATE users_customuser 
    SET country_id = NULL 
    WHERE country_id IS NOT NULL 
    AND country_id != '' 
    AND country_id GLOB '*[a-zA-Z]*'
""")
print(f"  Очищено записей: {cursor.rowcount}")

# Удаляем запись о последней проблемной миграции
cursor.execute("DELETE FROM django_migrations WHERE app = 'users' ORDER BY id DESC LIMIT 1;")
print("  Удалена последняя запись о миграции")

# Сохраняем изменения
conn.commit()

print("\n=== 5. Проверка ===")
cursor.execute("SELECT COUNT(*) FROM users_customuser WHERE country_id IS NOT NULL;")
count = cursor.fetchone()[0]
print(f"  Пользователей с country_id: {count}")

cursor.close()
conn.close()
print("\n✅ База данных исправлена!")