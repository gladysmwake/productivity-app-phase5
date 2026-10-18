"""SQLAlchemy models for the Productivity Notes API.

Defines the database schema and business logic:
- User: Account authentication entity with Bcrypt password security.
- Note: User-owned productivity resource with lifecycle cascade rules.
"""
from datetime import datetime, timezone

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import validates

from config import bcrypt, db


def utcnow():
    """Return timezone-aware current UTC time.
    Passed as a callable to SQLAlchemy columns so timestamp is evaluated on insert.
    """
    return datetime.now(timezone.utc)


class User(db.Model):
    """User account entity.

    Passwords are never stored in plain text. A bcrypt-generated salt + hash is
    persisted into `_password_hash`, and access is protected via a write-only property.
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    _password_hash = db.Column(db.String, nullable=False)

    # 1:M relationship with Note. Deleting a user cascades and removes all their notes.
    notes = db.relationship("Note", back_populates="user", cascade="all, delete-orphan")

    @hybrid_property
    def password_hash(self):
        """Write-only property: prevents reading or accidentally serializing the password hash."""
        raise AttributeError("password hashes cannot be viewed")

    @password_hash.setter
    def password_hash(self, password):
        """Salt and hash password using bcrypt before persisting."""
        self._password_hash = bcrypt.generate_password_hash(password.encode("utf-8")).decode("utf-8")

    def authenticate(self, password):
        """Verify candidate password against the stored bcrypt hash using constant-time comparison."""
        return bcrypt.check_password_hash(self._password_hash, password.encode("utf-8"))

    @validates("username")
    def validate_username(self, key, username):
        """Enforce username format, length, and case-insensitivity."""
        if not isinstance(username, str) or len(username.strip()) < 3:
            raise ValueError("Username must be at least 3 characters long")
        if len(username.strip()) > 50:
            raise ValueError("Username must be at most 50 characters long")
        # Normalize to lowercase so 'Echo' and 'echo' map to the same unique account
        return username.strip().lower()

    def __repr__(self):
        return f"<User {self.id}: {self.username}>"


class Note(db.Model):
    """Productivity note resource owned by a user."""
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    user = db.relationship("User", back_populates="notes")

    @validates("title", "content")
    def validate_not_blank(self, key, value):
        """Ensure title and content are non-empty strings and within maximum length."""
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{key.capitalize()} is required")
        if key == "title" and len(value.strip()) > 100:
            raise ValueError("Title must be at most 100 characters long")
        return value.strip()

    def __repr__(self):
        return f"<Note {self.id}: {self.title}>"
