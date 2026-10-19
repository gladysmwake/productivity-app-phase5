"""Shared helper functions and decorators for the Productivity Notes API."""
from functools import wraps

from flask import request, session
from marshmallow import ValidationError

from config import db
from models import Note, User

# cap per_page so a client can't request 10,000 rows at once
DEFAULT_PER_PAGE = 5
MAX_PER_PAGE = 50


def login_required(method):
    """Decorator for Flask-RESTful Resource methods enforcing session authentication.
    
    If the request does not carry a valid authenticated session, aborts with 401 Unauthorized
    before running the controller code.
    """
    @wraps(method)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return {"errors": ["Unauthorized"]}, 401
        return method(*args, **kwargs)

    return wrapper


def current_user():
    """Retrieve the currently authenticated User instance from the active session.
    
    Uses SQLAlchemy 2.0 `db.session.get()` for primary-key lookup.
    """
    user_id = session.get("user_id")
    return db.session.get(User, user_id) if user_id else None


def load_json(schema):
    """Parse and validate the incoming JSON body against a Marshmallow schema.

    Returns (data, None) on success or (None, (errors, status_code)) on failure.
    400 when the body isn't JSON, 422 when validation rules fail.
    """
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, ({"errors": ["Request body must be a JSON object"]}, 400)
    try:
        return schema.load(payload), None
    except ValidationError as err:
        errors = [f"{field}: {msg}" for field, msgs in err.messages.items() for msg in msgs]
        return None, ({"errors": errors}, 422)


def get_owned_note(note_id):
    """Fetch a note by ID and confirm the session user owns it.

    Returns (note, None) if everything checks out.
    Returns (None, error_response) with 404 if the note doesn't exist,
    or 403 if it belongs to someone else.
    """
    note = db.session.get(Note, note_id)
    if note is None:
        return None, ({"errors": ["Note not found"]}, 404)
    if note.user_id != session.get("user_id"):
        return None, ({"errors": ["You can only access your own notes"]}, 403)
    return note, None


def pagination_args():
    """Pull ?page and ?per_page from the query string and clamp them to safe ranges."""
    page = max(request.args.get("page", 1, type=int), 1)
    per_page = request.args.get("per_page", DEFAULT_PER_PAGE, type=int)
    return page, min(max(per_page, 1), MAX_PER_PAGE)
