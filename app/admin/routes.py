from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from ..models import User, Subject, Group, Schedule, TeacherGroupSubject
from ..extensions import db
from sqlalchemy import text, or_

admin_bp = Blueprint("admin", __name__, template_folder="../templates/admin")


@admin_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.role != "admin":
        return redirect(url_for("auth.login"))

    filter_group = request.args.get('group', '')
    filter_subject = request.args.get('subject', '')
    filter_week = request.args.get('week', '')

    users_count = User.query.count()
    students_count = User.query.filter_by(role="student").count()
    teachers_count = User.query.filter_by(role="teacher").count()

    all_teachers = User.query.filter_by(role="teacher").all()
    all_subjects = Subject.query.all()
    groups = Group.query.all()

    sched_query = Schedule.query
    if filter_group:
        sched_query = sched_query.filter_by(group_name=filter_group)
    if filter_subject:
        sched_query = sched_query.filter(Schedule.subject_name.ilike(f"%{filter_subject}%"))
    if filter_week and filter_week in ['Верхняя', 'Нижняя']:
        sched_query = sched_query.filter(or_(Schedule.week_type == filter_week, Schedule.week_type == 'Каждая'))
    schedules = sched_query.order_by(Schedule.day_of_week, Schedule.lesson_number).all()

    if filter_group:
        query = text("""
            SELECT DISTINCT s.id, s.name, s.teacher_ids_str 
            FROM subjects s
            JOIN teacher_groups_subjects tgs ON s.id = tgs.subject_id
            WHERE tgs.group_name = :group_name
        """)
        result = db.session.execute(query, {"group_name": filter_group}).fetchall()
        subjects = [{"id": row.id, "name": row.name, "teacher_ids_str": row.teacher_ids_str} for row in result]
    else:
        subjects = all_subjects

    return render_template("admin/dashboard.html",
                           users_count=users_count, students_count=students_count,
                           teachers_count=teachers_count, subjects=subjects,
                           all_teachers=all_teachers, groups=groups, schedules=schedules,
                           filter_group=filter_group, filter_subject=filter_subject, filter_week=filter_week,
                           all_subjects=all_subjects)


# --- УДАЛЕНИЕ ПОЛЬЗОВАТЕЛЯ (СТУДЕНТА ИЛИ ПРЕПОДАВАТЕЛЯ) ---
@admin_bp.route("/user/delete/<int:user_id>", methods=["POST"])
@login_required
def delete_user(user_id):
    if current_user.role != "admin":
        return redirect(url_for("auth.login"))

    user = User.query.get_or_404(user_id)
    if user.role == 'admin':
        flash("Нельзя удалить администратора!", "danger")
    else:
        db.session.delete(user)
        db.session.commit()
        flash(f"Пользователь {user.full_name} удален", "success")

    return redirect(request.referrer or url_for("admin.dashboard"))


# --- ПРЕДМЕТЫ ---
@admin_bp.route("/subject/add", methods=["POST"])
@login_required
def add_subject():
    name = request.form.get("name")
    if name:
        db.session.add(Subject(name=name))
        db.session.commit()
        flash(f"Предмет '{name}' добавлен", "success")
    return redirect(url_for("admin.dashboard", tab="subjects"))


@admin_bp.route("/subject/<int:subject_id>/assign", methods=["POST"])
@login_required
def assign_teachers(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    teacher_ids = request.form.getlist("teacher_ids")
    subject.teacher_ids_str = ",".join(teacher_ids) if teacher_ids else None
    db.session.commit()
    flash(f"Преподаватели для '{subject.name}' обновлены", "success")
    return redirect(url_for("admin.dashboard", tab="subjects"))


# --- ГРУППЫ ---
@admin_bp.route("/group/add", methods=["POST"])
@login_required
def add_group():
    name = request.form.get("group_name")
    if name and not Group.query.filter_by(name=name).first():
        new_group = Group(name=name)
        db.session.add(new_group)
        db.session.commit()
        flash(f"Группа '{name}' создана", "success")
    return redirect(url_for("admin.dashboard", tab="groups"))


@admin_bp.route("/student/add", methods=["POST"])
@login_required
def add_student():
    if current_user.role != "admin":
        return redirect(url_for("auth.login"))

    full_name = request.form.get("full_name")
    email = request.form.get("email")
    password = request.form.get("password")
    group_id = request.form.get("group_id")  # <-- ПОЛУЧАЕМ ID ГРУППЫ

    if full_name and email and password and group_id:
        # Проверяем, нет ли уже такого email
        if User.query.filter_by(email=email).first():
            flash("Студент с таким email уже существует!", "danger")
        else:
            # СОЗДАЕМ СТУДЕНТА И ЯВНО УКАЗЫВАЕМ group_id (через int)
            student = User(
                full_name=full_name,
                email=email,
                role="student",
                group_id=int(group_id)  # <-- ПРИВОДИМ К INT
            )
            student.set_password(password)
            db.session.add(student)
            db.session.commit()
            flash(f"Студент {full_name} добавлен", "success")
    else:
        flash("Заполните все поля!", "danger")

    return redirect(url_for("admin.dashboard", tab="students"))


# --- ПРЕПОДАВАТЕЛИ ---
@admin_bp.route("/teacher/add", methods=["POST"])
@login_required
def add_teacher():
    full_name = request.form.get("full_name")
    email = request.form.get("email")
    password = request.form.get("password")  # <-- ПОЛУЧАЕМ ПАРОЛЬ

    if full_name and email and password:
        if User.query.filter_by(email=email).first():
            flash("Преподаватель с таким email уже существует!", "danger")
        else:
            teacher = User(full_name=full_name, email=email, role="teacher")
            teacher.set_password(password)  # <-- УСТАНАВЛИВАЕМ ПАРОЛЬ
            db.session.add(teacher)
            db.session.commit()
            flash(f"Преподаватель {full_name} добавлен", "success")
    return redirect(url_for("admin.dashboard", tab="teachers"))


# --- РАСПИСАНИЕ ---
@admin_bp.route("/schedule/add", methods=["POST"])
@login_required
def add_schedule():
    group_name = request.form.get("group_name")
    day = request.form.get("day")
    lesson = request.form.get("lesson")
    subject = request.form.get("subject")
    teacher = request.form.get("teacher")
    room = request.form.get("room")
    week_type = request.form.get("week_type")

    if group_name and day and lesson and subject:
        sched = Schedule(group_name=group_name, day_of_week=day, lesson_number=int(lesson),
                         subject_name=subject, teacher_name=teacher, room=room, week_type=week_type)
        db.session.add(sched)
        db.session.commit()
        flash("Занятие добавлено", "success")
    return redirect(url_for("admin.dashboard", tab="schedule"))


@admin_bp.route("/schedule/delete/<int:sch_id>", methods=["POST"])
@login_required
def delete_schedule(sch_id):
    sched = Schedule.query.get_or_404(sch_id)
    db.session.delete(sched)
    db.session.commit()
    flash("Занятие удалено", "info")
    return redirect(url_for("admin.dashboard", tab="schedule"))