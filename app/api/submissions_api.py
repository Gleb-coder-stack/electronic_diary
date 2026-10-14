from datetime import datetime
from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from ..models import Submission
from ..extensions import db

submissions_api_bp = Blueprint("submissions_api", __name__)


@submissions_api_bp.route("/", methods=["GET"])
@login_required
def my_submissions():
    subs = (Submission.query
            .filter_by(student_id=current_user.id)
            .all())
    return jsonify([_serialize(s) for s in subs])


@submissions_api_bp.route("/<int:sub_id>/toggle", methods=["POST"])
@login_required
def toggle(sub_id):
    sub = Submission.query.get_or_404(sub_id)
    if sub.student_id != current_user.id:
        return jsonify({"error": "Доступ запрещён"}), 403

    sub.is_completed = not sub.is_completed
    sub.completed_at = datetime.utcnow() if sub.is_completed else None
    db.session.commit()

    return jsonify({
        "id": sub.id,
        "is_completed": sub.is_completed,
        "color": "#4CAF50" if sub.is_completed else "#F44336"
    })


def _serialize(s):
    return {
        "id": s.id,
        "task_id": s.task_id,
        "subject": s.task.subject.name if s.task.subject else None,
        "title": s.task.title,
        "start": s.task.start_date.strftime("%Y-%m-%d"),
        "end": s.task.due_date.strftime("%Y-%m-%d"),
        "is_completed": s.is_completed
    }