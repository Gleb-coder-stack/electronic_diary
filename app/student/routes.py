from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from ..models import Task, Submission
from ..gantt.builder import build_gantt_data

student_bp = Blueprint("student", __name__, template_folder="../templates/student")


@student_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.role != "student":
        return redirect(url_for("auth.login"))

    subs = (Submission.query.join(Task)
            .filter(Submission.student_id == current_user.id)
            .order_by(Task.due_date).all())

    return render_template("student/dashboard.html",
                           submissions=subs,
                           gantt_data=build_gantt_data(subs))