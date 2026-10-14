from flask import Flask
from .extensions import db, login_manager, migrate
from .config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Модули (blueprints)
    from .auth.routes import auth_bp
    from .teacher.routes import teacher_bp
    from .student.routes import student_bp
    from .api.auth_api import auth_api_bp
    from .api.tasks_api import tasks_api_bp
    from .api.submissions_api import submissions_api_bp
    from .api.stats_api import stats_api_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(teacher_bp, url_prefix="/teacher")
    app.register_blueprint(student_bp, url_prefix="/student")

    app.register_blueprint(auth_api_bp, url_prefix="/api/auth")
    app.register_blueprint(tasks_api_bp, url_prefix="/api/tasks")
    app.register_blueprint(submissions_api_bp, url_prefix="/api/submissions")
    app.register_blueprint(stats_api_bp, url_prefix="/api/stats")

    return app