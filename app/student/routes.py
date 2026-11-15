from flask import Blueprint, render_template, redirect, url_for, request, send_from_directory, current_app
from flask_login import login_required, current_user
from ..models import Task, Submission, Subject
from ..gantt.builder import build_gantt_data
from sqlalchemy import or_
import os

student_bp = Blueprint("student", __name__, template_folder="../templates/student")


@student_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.role != "student":
        return redirect(url_for("auth.login"))

    subject_id = request.args.get('subject_id')
    week_filter = request.args.get('week', '')

    query = Submission.query.join(Task).filter(Submission.student_id == current_user.id)

    if subject_id and subject_id.isdigit():
        query = query.filter(Task.subject_id == int(subject_id))

    # ИСПРАВЛЕНИЕ: Оставляем задания "Каждая" и выбранную неделю
    if week_filter:
        query = query.filter(or_(Task.week_type == week_filter, Task.week_type == 'Каждая'))

    subs = query.order_by(Task.due_date).all()

    subjects = Subject.query.join(Task).join(Submission).filter(
        Submission.student_id == current_user.id
    ).distinct().all()

    return render_template("student/dashboard.html",
                           submissions=subs,
                           gantt_data=build_gantt_data(subs),
                           subjects=subjects,
                           current_subject=subject_id,
                           current_week=week_filter)


@student_bp.route("/download/<filename>")
@login_required
def download_file(filename):
    upload_folder = os.path.join(current_app.root_path, '..', 'uploads')
    task = Task.query.filter_by(file_path=filename).first()
    download_name = task.title if task else filename
    return send_from_directory(upload_folder, filename, as_attachment=True, download_name=download_name)