from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from ..models import Task

stats_api_bp = Blueprint("stats_api", __name__)


@stats_api_bp.route("/teacher", methods=["GET"])
@login_required
def teacher_stats():
    if current_user.role != "teacher":
        return jsonify({"error": "Доступ запрещён"}), 403

    tasks = Task.query.filter_by(teacher_id=current_user.id).all()
    return jsonify([{
        "task_id": t.id,
        "title": t.title,
        "subject": t.subject.name if t.subject else None,
        "completed": sum(1 for s in t.submissions if s.is_completed),
        "total": len(t.submissions)
    } for t in tasks])