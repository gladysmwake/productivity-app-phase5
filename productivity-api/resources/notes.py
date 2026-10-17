from flask import session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import db
from models import Note
from schemas import NoteSchema, note_schema, notes_schema
from utils import get_owned_note, load_json, login_required, pagination_args


class NoteList(Resource):
    @login_required
    def get(self):
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
    @login_required
    def get(self, note_id):
        note, error = get_owned_note(note_id)
        if error:
            return error
        return note_schema.dump(note), 200

    @login_required
    def patch(self, note_id):
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
            return {"errors": [str(e)]}, 422

    @login_required
    def delete(self, note_id):
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
