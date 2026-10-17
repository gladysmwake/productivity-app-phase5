from marshmallow import EXCLUDE, Schema, ValidationError, fields, validate


def not_blank(value):
    if not value.strip():
        raise ValidationError("Cannot be blank")


class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(dump_only=True)


class SignupSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    username = fields.Str(required=True, validate=[validate.Length(min=3, max=50), not_blank])
    password = fields.Str(required=True, validate=[validate.Length(min=6, max=128), not_blank])


class LoginSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    username = fields.Str(required=True)
    password = fields.Str(required=True)


class NoteSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Int(dump_only=True)
    title = fields.Str(required=True, validate=[validate.Length(max=100), not_blank])
    content = fields.Str(required=True, validate=not_blank)
    created_at = fields.DateTime(dump_only=True)
    user_id = fields.Int(dump_only=True)


user_schema = UserSchema()
note_schema = NoteSchema()
notes_schema = NoteSchema(many=True)
