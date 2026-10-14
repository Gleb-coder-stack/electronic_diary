from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from ..models import Task, Subject, User, Submission
from ..extensions import db

tasks_api_bp = Blueprint("tasks_api", __name__)


@tasks_api_bp.route("/", methods=["GET"])
@login_required
def list_tasks():
    if current_user.role == "teacher":
        tasks = Task.query.filter_by(teacher_id=current_user.id).all()
    else:
        tasks = (Task.query.join(Submission)
                 .filter(Submission.student_id == current_user.id).all())
    return jsonify([_serialize(t) for t in tasks])


@tasks_api_bp.route("/", methods=["POST"])
@login_required
def create_task():
    if current_user.role != "teacher":
        return jsonify({"error": "Доступ запрещён"}), 403

    data = request.get_json()
    task = Task(
        title=data["title"],
        description=data.get("description", ""),
        subject_id=data["subject_id"],
        teacher_id=current_user.id,
        group_name=data["group_name"],
        due_date=datetime.strptime(data["due_date"], "%Y-%m-%d").date()
    )
    db.session.add(task)
    db.session.commit()

    students = User.query.filter_by(role="student", group_name=task.group_name).all()
    for s in students:
        db.session.add(Submission(task_id=task.id, student_id=s.id))
    db.session.commit()

    return jsonify(_serialize(task)), 201


@tasks_api_bp.route("/<int:task_id>", methods=["PUT"])
@login_required
def update_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.teacher_id != current_user.id:
        return jsonify({"error": "Доступ запрещён"}), 403

    data = request.get_json()
    task.title = data.get("title", task.title)
    task.description = data.get("description", task.description)
    task.due_date = datetime.strptime(data["due_date"], "%Y-%m-%d").date() \
        if data.get("due_date") else task.due_date
    db.session.commit()
    return jsonify(_serialize(task))


@tasks_api_bp.route("/<int:task_id>", methods=["DELETE"])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.teacher_id != current_user.id:
        return jsonify({"error": "Доступ запрещён"}), 403
    db.session.delete(task)
    db.session.commit()
    return jsonify({"status": "deleted"})


def _serialize(t):
    return {
        "id": t.id,
        "title": t.title,
        "description": t.description,
        "subject": t.subject.name if t.subject else None,
        "group": t.group_name,
        "start": t.start_date.strftime("%Y-%m-%d"),
        "end": t.due_date.strftime("%Y-%m-%d"),
        "completed_count": sum(1 for s in t.submissions if s.is_completed),
        "total_count": len(t.submissions)
    }