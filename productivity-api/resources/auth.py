"""Authentication controllers: Signup, Login, Logout, and Session Verification."""
from flask import session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import db
from models import User
from schemas import LoginSchema, SignupSchema, user_schema
from utils import current_user, load_json, login_required


class Signup(Resource):
    """User registration endpoint.
    
    Accepts `username` and `password`, validates length and format, hashes the password
    with bcrypt, and establishes a new authenticated session.
    """

    def post(self):
        data, error = load_json(SignupSchema())
        if error:
            return error

        try:
            user = User(username=data["username"])
            user.password_hash = data["password"]
            db.session.add(user)
            db.session.commit()
        except ValueError as e:
            db.session.rollback()
            return {"errors": [str(e)]}, 422
        except IntegrityError:
            db.session.rollback()
            return {"errors": ["Username is already taken"]}, 422

        # wipe any leftover session data before writing the new user in
        session.clear()
        session["user_id"] = user.id
        return user_schema.dump(user), 201


class Login(Resource):
    """User authentication endpoint.
    
    Verifies credentials and issues a signed session cookie.
    """

    def post(self):
        data, error = load_json(LoginSchema())
        if error:
            return error

        # usernames are stored lowercase, so normalize before querying
        user = User.query.filter_by(username=data["username"].strip().lower()).first()
        if user and user.authenticate(data["password"]):
            # clear the old session first so we start fresh
            session.clear()
            session["user_id"] = user.id
            return user_schema.dump(user), 200

        # keep the message vague so an attacker can't tell which field was wrong
        return {"errors": ["Invalid username or password"]}, 401


class Logout(Resource):
    """Session termination endpoint.
    
    Invalidates the active session and returns HTTP 204 No Content.
    """

    @login_required
    def delete(self):
        session.clear()
        return {}, 204


class CheckSession(Resource):
    """Session persistence endpoint (mapped to /check_session and /me).
    
    Allows client applications to restore login state on browser refresh.
    """

    def get(self):
        user = current_user()
        if user:
            return user_schema.dump(user), 200
        session.clear()
        return {"errors": ["Unauthorized"]}, 401
