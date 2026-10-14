from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..models import Task, Subject, User, Submission
from ..extensions import db

teacher_bp = Blueprint("teacher", __name__, template_folder="../templates/teacher")


@teacher_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.role != "teacher":
        return redirect(url_for("auth.login"))
    tasks = Task.query.filter_by(teacher_id=current_user.id).order_by(Task.due_date).all()
    return render_template("teacher/dashboard.html", tasks=tasks)


@teacher_bp.route("/task/create", methods=["GET", "POST"])
@login_required
def create_task():
    if current_user.role != "teacher":
        return redirect(url_for("auth.login"))

    subjects = Subject.query.filter_by(teacher_id=current_user.id).all()

    if request.method == "POST":
        task = Task(
            title=request.form["title"],
            description=request.form["description"],
            subject_id=request.form["subject_id"],
            teacher_id=current_user.id,
            group_name=request.form["group_name"],
            due_date=datetime.strptime(request.form["due_date"], "%Y-%m-%d").date()
        )
        db.session.add(task)
        db.session.commit()

        students = User.query.filter_by(role="student", group_name=task.group_name).all()
        for s in students:
            db.session.add(Submission(task_id=task.id, student_id=s.id))
        db.session.commit()

        flash("Задание успешно создано", "success")
        return redirect(url_for("teacher.dashboard"))

    return render_template("teacher/create_task.html", subjects=subjects)