from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_user
from werkzeug.security import check_password_hash


def init_api(app, db, Post, User) -> None:
    """
    Подключает API в существующее Flask-приложение.
    """

    api_bp = Blueprint("api", __name__, url_prefix="/api")

    def _json_error(message: str, status: int = 400):
        return jsonify({"ok": False, "error": message}), status

    def _post_to_dict(post) -> dict[str, Any]:
        return {
            "id": post.id,
            "title": post.title,
            "text": post.text,
            "views": post.views,
            "date": post.date
        }

    @api_bp.get("/posts")
    def list_posts():
        posts = Post.query.order_by(Post.views.desc()).all()
        return jsonify({"ok": True, "items": [_post_to_dict(p) for p in posts]})

    @api_bp.get("/posts/<int:post_id>")
    def get_posts(post_id: int):
        post = db.session.get(Post, post_id)
        if post is None:
            return _json_error("Post not found", 404)
        return jsonify({"ok": True, "item": _post_to_dict(post)})

    @api_bp.post("/auth/login")
    def login():
        payload = request.get_json(silent=True) or {}
        username = payload.get("username")
        password = payload.get("password")

        if not username or not password:
            return _json_error("username and password are required", 400)

        user = User.query.filter_by(username=username).first()
        if user is None:
            return _json_error("User not found", 404)
        if not check_password_hash(user.password, password):
            return _json_error("Invalid credentials", 401)

        login_user(user)
        return jsonify({"ok": True, "message": "Login successful"})

    def _require_admin():
        if not current_user.is_authenticated:
            return _json_error("Authentication required", 401)
        if not getattr(current_user, "admin", False):
            return _json_error("Admin privileges required", 403)
        return None

    @api_bp.post("/posts")
    def create_post():
        err = _require_admin()
        if err is not None:
            return err

        payload = request.get_json(silent=True) or {}
        title = payload.get("title")
        text = payload.get("text")

        if not title or not text:
            return _json_error("title and text are required", 400)

        post = Post(id_author=current_user.id, title=title, text=text, categories=[], image_name=None)
        db.session.add(post)
        db.session.commit()
        return jsonify({"ok": True, "item": _post_to_dict(post)}), 201

    @api_bp.delete("/posts/<int:post_id>")
    def delete_post(post_id: int):
        err = _require_admin()
        if err is not None:
            return err

        post = db.session.get(Post, post_id)
        if post is None:
            return _json_error("Post not found", 404)

        db.session.delete(post)
        db.session.commit()
        return jsonify({"ok": True, "message": "Deleted"})

    # Регистрируем blueprint в приложение
    app.register_blueprint(api_bp)

