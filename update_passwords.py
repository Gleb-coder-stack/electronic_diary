from app import create_app
from app.extensions import db
from app.models import User

app = create_app()

with app.app_context():
    password = "12345"
    users = User.query.all()
    for u in users:
        u.set_password(password)
    db.session.commit()
    print(f"✅ Пароли обновлены для {len(users)} пользователей")