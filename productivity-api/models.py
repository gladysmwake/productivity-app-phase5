from datetime import datetime, timezone

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import validates

from config import bcrypt, db


def utcnow():
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    _password_hash = db.Column(db.String, nullable=False)

    notes = db.relationship("Note", back_populates="user", cascade="all, delete-orphan")

    @hybrid_property
    def password_hash(self):
        raise AttributeError("password hashes cannot be viewed")

    @password_hash.setter
    def password_hash(self, password):
        self._password_hash = bcrypt.generate_password_hash(password.encode("utf-8")).decode("utf-8")

    def authenticate(self, password):
        return bcrypt.check_password_hash(self._password_hash, password.encode("utf-8"))

    @validates("username")
    def validate_username(self, key, username):
        if not isinstance(username, str) or len(username.strip()) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if len(username.strip()) > 50:
            raise ValueError("Username must be at most 50 characters long")
        return username.strip().lower()

    def __repr__(self):
        return f"<User {self.id}: {self.username}>"


class Note(db.Model):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    user = db.relationship("User", back_populates="notes")

    @validates("title", "content")
    def validate_not_blank(self, key, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{key.capitalize()} is required")
        if key == "title" and len(value.strip()) > 100:
            raise ValueError("Title must be at most 100 characters long")
        return value.strip()

    def __repr__(self):
        return f"<Note {self.id}: {self.title}>"
