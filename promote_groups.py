from app import create_app
from app.extensions import db
from app.models import Group, User

app = create_app()

with app.app_context():
    groups = Group.query.all()
    for g in groups:
        # Ищем цифры в названии (например, ИСП.25А)
        import re

        match = re.search(r'(\d{2})', g.name)
        if match:
            year = int(match.group(1))
            new_year = year - 1  # Группа 25 -> 24 (переход на следующий курс)
            new_name = g.name.replace(str(year), str(new_year))

            # Обновляем название группы
            old_name = g.name
            g.name = new_name

            # Обновляем привязку у студентов
            students = User.query.filter_by(group_id=g.id).all()
            for s in students:
                s.group_name = new_name  # Если поле осталось

            print(f"Группа {old_name} переведена на {new_name}")

    db.session.commit()
    print("Все группы переведены на следующий курс!")