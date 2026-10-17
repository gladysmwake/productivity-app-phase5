from flask import session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import db
from models import User
from schemas import LoginSchema, SignupSchema, user_schema
from utils import current_user, load_json, login_required


class Signup(Resource):
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

        session.clear()
        session["user_id"] = user.id
        return user_schema.dump(user), 201


class Login(Resource):
    def post(self):
        data, error = load_json(LoginSchema())
        if error:
            return error

        user = User.query.filter_by(username=data["username"].strip().lower()).first()
        if user and user.authenticate(data["password"]):
            session.clear()
            session["user_id"] = user.id
            return user_schema.dump(user), 200

        return {"errors": ["Invalid username or password"]}, 401


class Logout(Resource):
    @login_required
    def delete(self):
        session.clear()
        return {}, 204


class CheckSession(Resource):
    def get(self):
        user = current_user()
        if user:
            return user_schema.dump(user), 200
        session.clear()
        return {"errors": ["Unauthorized"]}, 401
