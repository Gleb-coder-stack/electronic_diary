from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Выполняем прямой SQL-запрос к PostgreSQL
        db.session.execute(text('ALTER TABLE subjects ADD COLUMN teacher_ids_str VARCHAR(255);'))
        db.session.commit()
        print("✅ УСПЕХ: Колонка teacher_ids_str добавлена в базу данных!")
    except Exception as e:
        if "already exists" in str(e) or "уже существует" in str(e):
            print("ℹ️ Колонка teacher_ids_str уже существует. Всё в порядке!")
        else:
            print(f"❌ ОШИБКА: {e}")