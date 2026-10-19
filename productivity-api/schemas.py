"""Marshmallow schemas for request validation and response serialization."""
from marshmallow import EXCLUDE, Schema, ValidationError, fields, validate, validates_schema


def not_blank(value):
    """Reject strings that are empty or consist solely of whitespace characters."""
    if not value.strip():
        raise ValidationError("Cannot be blank")


class UserSchema(Schema):
    """Public user serializer. Never serializes password hashes or internal secrets."""
    id = fields.Int(dump_only=True)
    username = fields.Str(dump_only=True)


class SignupSchema(Schema):
    """Validation schema for user registration payloads."""
    class Meta:
        # Prevent mass-assignment vulnerabilities by discarding unknown keys
        unknown = EXCLUDE

    username = fields.Str(required=True, validate=[validate.Length(min=3, max=50), not_blank])
    password = fields.Str(required=True, validate=[validate.Length(min=6, max=128), not_blank])
    # The client-with-sessions frontend sends password_confirmation; optional for direct API callers
    password_confirmation = fields.Str()

    @validates_schema
    def check_confirmation(self, data, **kwargs):
        confirmation = data.get("password_confirmation")
        if confirmation is not None and confirmation != data.get("password"):
            raise ValidationError("Passwords do not match", "password_confirmation")


class LoginSchema(Schema):
    """Validation schema for user login credentials."""
    class Meta:
        unknown = EXCLUDE

    username = fields.Str(required=True)
    password = fields.Str(required=True)


class NoteSchema(Schema):
    """Validation and serialization schema for Note resources."""
    class Meta:
        unknown = EXCLUDE

    # dump_only fields can only be sent in responses, never written by clients
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True, validate=[validate.Length(max=100), not_blank])
    content = fields.Str(required=True, validate=not_blank)
    created_at = fields.DateTime(dump_only=True)
    user_id = fields.Int(dump_only=True)


user_schema = UserSchema()
note_schema = NoteSchema()
notes_schema = NoteSchema(many=True)
