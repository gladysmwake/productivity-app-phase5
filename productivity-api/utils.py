from functools import wraps

from flask import request, session
from marshmallow import ValidationError

from config import db
from models import Note, User

DEFAULT_PER_PAGE = 5
MAX_PER_PAGE = 50


def login_required(method):
    @wraps(method)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return {"errors": ["Unauthorized"]}, 401
        return method(*args, **kwargs)

    return wrapper


def current_user():
    user_id = session.get("user_id")
    return db.session.get(User, user_id) if user_id else None


def load_json(schema):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, ({"errors": ["Request body must be a JSON object"]}, 400)
    try:
        return schema.load(payload), None
    except ValidationError as err:
        errors = [f"{field}: {msg}" for field, msgs in err.messages.items() for msg in msgs]
        return None, ({"errors": errors}, 422)


def get_owned_note(note_id):
    note = db.session.get(Note, note_id)
    if note is None:
        return None, ({"errors": ["Note not found"]}, 404)
    if note.user_id != session.get("user_id"):
        return None, ({"errors": ["You can only access your own notes"]}, 403)
    return note, None


def pagination_args():
    page = max(request.args.get("page", 1, type=int), 1)
    per_page = request.args.get("per_page", DEFAULT_PER_PAGE, type=int)
    return page, min(max(per_page, 1), MAX_PER_PAGE)
