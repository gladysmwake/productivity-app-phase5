from config import api
from resources.auth import CheckSession, Login, Logout, Signup
from resources.notes import NoteDetail, NoteList


def register_routes():
    api.add_resource(Signup, "/signup")
    api.add_resource(Login, "/login")
    api.add_resource(Logout, "/logout")
    api.add_resource(CheckSession, "/check_session", "/me")
    api.add_resource(NoteList, "/notes")
    api.add_resource(NoteDetail, "/notes/<int:note_id>")
