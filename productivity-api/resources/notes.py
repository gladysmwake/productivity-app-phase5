"""Note controllers: Paginated list, creation, retrieval, updates, and deletion."""
from flask import session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import db
from models import Note
from schemas import NoteSchema, note_schema, notes_schema
from utils import get_owned_note, load_json, login_required, pagination_args


class NoteList(Resource):
    """Collection endpoint for the user's notes (/notes)."""

    @login_required
    def get(self):
        """List the authenticated user's notes with server-side pagination.
        
        Filters strictly by `user_id=session['user_id']` at the SQL level, ensuring
        users can never query or receive another user's records.
        """
        page, per_page = pagination_args()
        pagination = (
            Note.query.filter_by(user_id=session["user_id"])
            .order_by(Note.created_at.desc(), Note.id.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )
        return {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "notes": notes_schema.dump(pagination.items),
        }, 200

    @login_required
    def post(self):
        """Create a new note. user_id comes from the session, not the request body."""
        data, error = load_json(NoteSchema())
        if error:
            return error

        try:
            note = Note(title=data["title"], content=data["content"], user_id=session["user_id"])
            db.session.add(note)
            db.session.commit()
            return note_schema.dump(note), 201
        except ValueError as e:
            db.session.rollback()
            return {"errors": [str(e)]}, 422
        except IntegrityError:
            db.session.rollback()
            return {"errors": ["Failed to create note"]}, 422


class NoteDetail(Resource):
    """Item endpoint for individual note operations (/notes/<int:note_id>)."""

    @login_required
    def get(self, note_id):
        """Retrieve a single note, verifying ownership."""
        note, error = get_owned_note(note_id)
        if error:
            return error
        return note_schema.dump(note), 200

    @login_required
    def patch(self, note_id):
        """Partially update a note's title and/or content.
        
        Uses `partial=True` to allow either title or content to be updated independently.
        """
        note, error = get_owned_note(note_id)
        if error:
            return error

        data, error = load_json(NoteSchema(partial=True))
        if error:
            return error

        try:
            for field, value in data.items():
                setattr(note, field, value)
            db.session.commit()
            return note_schema.dump(note), 200
        except ValueError as e:
            db.session.rollback()
            return {"errors": [str(e)]}, 422
        except IntegrityError:
            db.session.rollback()
            return {"errors": ["Failed to update note"]}, 422

    @login_required
    def delete(self, note_id):
        """Permanently delete a note owned by the authenticated user."""
        note, error = get_owned_note(note_id)
        if error:
            return error

        try:
            db.session.delete(note)
            db.session.commit()
            return {}, 204
        except IntegrityError:
            db.session.rollback()
            return {"errors": ["Failed to delete note"]}, 422
