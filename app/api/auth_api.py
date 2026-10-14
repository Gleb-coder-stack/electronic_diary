from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, current_user
from ..models import User

auth_api_bp = Blueprint("auth_api", __name__)

@auth_api_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get("email")).first()
    if user and user.check_password(data.get("password")):
        login_user(user)
        return jsonify({"status": "ok", "role": user.role, "name": user.full_name})
    return jsonify({"status": "error", "message": "Неверный логин или пароль"}), 401


@auth_api_bp.route("/me")
def me():
    if not current_user.is_authenticated:
        return jsonify({"authenticated": False}), 401
    return jsonify({
        "id": current_user.id,
        "name": current_user.full_name,
        "role": current_user.role,
        "group": current_user.group_name
    })


@auth_api_bp.route("/logout", methods=["POST"])
def logout():
    logout_user()
    return jsonify({"status": "ok"})