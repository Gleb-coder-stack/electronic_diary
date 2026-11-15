from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from ..models import Task, Subject, User, Submission, Group
from ..extensions import db
from sqlalchemy import text, or_
import os, uuid
from datetime import datetime
from werkzeug.utils import secure_filename

teacher_bp = Blueprint("teacher", __name__, template_folder="../templates/teacher")


@teacher_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.role != "teacher":
        return redirect(url_for("auth.login"))

    subject_id = request.args.get('subject_id')
    week_filter = request.args.get('week', '')

    tasks_query = Task.query.filter_by(teacher_id=current_user.id)

    if subject_id and subject_id.isdigit():
        tasks_query = tasks_query.filter_by(subject_id=int(subject_id))

    # ИСПРАВЛЕНИЕ: Оставляем задания "Каждая" и выбранную неделю
    if week_filter:
        tasks_query = tasks_query.filter(or_(Task.week_type == week_filter, Task.week_type == 'Каждая'))

    tasks = tasks_query.order_by(Task.due_date).all()

    my_subjects_query = text("""
        SELECT DISTINCT s.id, s.name 
        FROM subjects s
        JOIN teacher_groups_subjects tgs ON s.id = tgs.subject_id
        WHERE tgs.teacher_id = :tid
    """)
    my_subjects = db.session.execute(my_subjects_query, {"tid": current_user.id}).fetchall()

    task_data = []
    for t in tasks:
        students_info = []
        for sub in t.submissions:
            student = User.query.get(sub.student_id)
            if student:
                students_info.append({"name": student.full_name, "is_completed": sub.is_completed})
        task_data.append({
            "task": t, "students": students_info,
            "completed_count": sum(1 for s in students_info if s["is_completed"]),
            "total_count": len(students_info)
        })

    return render_template("teacher/dashboard.html", task_data=task_data, subjects=my_subjects,
                           current_subject=subject_id, current_week=week_filter)


@teacher_bp.route("/task/create", methods=["GET", "POST"])
@login_required
def create_task():
    if current_user.role != "teacher":
        return redirect(url_for("auth.login"))

    my_subjects_query = text("""
        SELECT DISTINCT s.id, s.name 
        FROM subjects s
        JOIN teacher_groups_subjects tgs ON s.id = tgs.subject_id
        WHERE tgs.teacher_id = :tid
    """)
    my_subjects = db.session.execute(my_subjects_query, {"tid": current_user.id}).fetchall()

    links_query = text("SELECT subject_id, group_name FROM teacher_groups_subjects WHERE teacher_id = :tid")
    links = db.session.execute(links_query, {"tid": current_user.id}).fetchall()

    subject_groups = {}
    for row in links:
        subj_id = str(row.subject_id)
        if subj_id not in subject_groups: subject_groups[subj_id] = []
        subject_groups[subj_id].append(row.group_name)

    if request.method == "POST":
        file = request.files.get('file')
        file_path = None

        if file and file.filename != '':
            ext = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid.uuid4().hex}{ext}"
            upload_folder = os.path.join(current_app.root_path, '..', 'uploads')
            if not os.path.exists(upload_folder): os.makedirs(upload_folder)
            file.save(os.path.join(upload_folder, unique_filename))
            file_path = unique_filename

        group_name = request.form["group_name"]

        task = Task(
            title=request.form["title"],
            subject_id=request.form["subject_id"],
            teacher_id=current_user.id,
            group_name=group_name,
            due_date=datetime.strptime(request.form["due_date"], "%Y-%m-%d").date(),
            file_path=file_path,
            week_type=request.form.get("week_type", "Каждая")  # <-- СОХРАНЯЕМ НЕДЕЛЮ
        )
        db.session.add(task)
        db.session.commit()

        group = Group.query.filter_by(name=group_name).first()
        if group:
            students = User.query.filter_by(role="student", group_id=group.id).all()
            for s in students:
                db.session.add(Submission(task_id=task.id, student_id=s.id))
            db.session.commit()

        flash("Задание успешно создано", "success")
        return redirect(url_for("teacher.dashboard"))

    return render_template("teacher/create_task.html", subjects=my_subjects, subject_groups=subject_groups)


@teacher_bp.route("/task/edit/<int:task_id>", methods=["GET", "POST"])
@login_required
def edit_task(task_id):
    if current_user.role != "teacher": return redirect(url_for("auth.login"))
    task = Task.query.get_or_404(task_id)

    if request.method == "POST":
        file = request.files.get('file')
        task.title = request.form["title"]
        task.subject_id = request.form["subject_id"]
        task.group_name = request.form["group_name"]
        task.due_date = datetime.strptime(request.form["due_date"], "%Y-%m-%d").date()
        task.week_type = request.form.get("week_type", "Каждая")  # <-- ОБНОВЛЯЕМ НЕДЕЛЮ

        if file and file.filename != '':
            ext = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid.uuid4().hex}{ext}"
            upload_folder = os.path.join(current_app.root_path, '..', 'uploads')
            file.save(os.path.join(upload_folder, unique_filename))
            task.file_path = unique_filename

        db.session.commit()
        flash("Задание успешно обновлено", "success")
        return redirect(url_for("teacher.dashboard"))

    all_subjects = Subject.query.all()
    all_groups = Group.query.all()
    return render_template("teacher/edit_task.html", task=task, subjects=all_subjects, groups=all_groups)


@teacher_bp.route("/task/delete/<int:task_id>", methods=["POST"])
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.teacher_id == current_user.id:
        db.session.delete(task)
        db.session.commit()
    return redirect(url_for("teacher.dashboard"))