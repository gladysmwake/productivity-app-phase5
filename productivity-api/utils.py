"""Shared helper functions and decorators for the Productivity Notes API."""
from functools import wraps

from flask import request, session
from marshmallow import ValidationError

from config import db
from models import Note, User

# Pagination defaults: prevent client-side denial-of-service through unbounded queries.
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
    """Safely parse and validate the incoming request JSON payload against a Marshmallow schema.
    
    Returns:
        tuple: (validated_data, None) on success, or (None, (error_dict, status_code)) on failure.
        - 400 Bad Request: If payload is missing or not a JSON object.
        - 422 Unprocessable Entity: If field validation rules fail.
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
    """Retrieve a note and enforce row-level access control.
    
    Returns:
        tuple: (note, None) if found and owned by session user.
        - 404 Not Found: If note does not exist in the database.
        - 403 Forbidden: If note exists but belongs to a different user.
    """
    note = db.session.get(Note, note_id)
    if note is None:
        return None, ({"errors": ["Note not found"]}, 404)
    if note.user_id != session.get("user_id"):
        return None, ({"errors": ["You can only access your own notes"]}, 403)
    return note, None


def pagination_args():
    """Extract, parse, and clamp pagination query parameters (?page=1&per_page=5).
    
    Clamps `page >= 1` and `1 <= per_page <= MAX_PER_PAGE (50)` to ensure database query safety.
    """
    page = max(request.args.get("page", 1, type=int), 1)
    per_page = request.args.get("per_page", DEFAULT_PER_PAGE, type=int)
    return page, min(max(per_page, 1), MAX_PER_PAGE)
