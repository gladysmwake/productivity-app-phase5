# Productivity Notes API

A secure, session-based Flask REST API that lets users sign up, log in, and
manage their own private notes. Every resource endpoint is protected so that a
user can only read or modify their own data.

---

## Project Description

This backend was built as the API layer for a productivity tool. It provides:

- **Full authentication** - sign-up, login, logout and session check
  (cookie-based sessions, no JWT).
- **Password security** - passwords are hashed with Flask-Bcrypt; the raw
  value is never stored or exposed.
- **User-owned notes** - each note belongs to exactly one user. Other users
  receive a 403 response if they try to access it.
- **Full CRUD** - create, read (single + paginated list), update and delete.
- **Pagination** - the list endpoint accepts `page` and `per_page` query
  parameters (`per_page` is capped at 50).

---

## Tech Stack

| Layer | Package |
|---|---|
| Web framework | Flask 2.2.2 + Flask-RESTful 0.3.9 |
| ORM | Flask-SQLAlchemy 3.0.3 |
| Migrations | Flask-Migrate 4.0.0 |
| Password hashing | Flask-Bcrypt 1.0.1 |
| Serialisation / validation | marshmallow 3.20.1 |
| Test data | Faker 15.3.2 |
| Test runner | pytest 7.2.0 |
| WSGI | Werkzeug 2.2.2 |

---

## Installation

Requires **Python 3.8+** and **Pipenv**.

```bash
# 1. Clone the repo and enter the API directory
git clone <your-repo-url>
cd productivity-app-phase5/productivity-api

# 2. Create the virtual environment and install all dependencies
pipenv install

# 3. Activate the virtual environment
pipenv shell

# 4. Point Flask at the application
export FLASK_APP=app.py        # macOS / Linux
set FLASK_APP=app.py           # Windows CMD
$env:FLASK_APP = "app.py"     # Windows PowerShell

# 5. Apply the database migrations (creates the SQLite file)
flask db upgrade

# 6. Seed the database with example users and notes
python seed.py
```

seed.py creates three users - **echo**, **amanda** and **wanjiku** - each
with the password `password123`, and 12 notes per user (36 notes total).

---

## Running the Server

```bash
# Option A - Flask dev server (auto-reloads on file changes)
flask run -p 5555

# Option B - directly via Python
python app.py
```

The API is available at http://127.0.0.1:5555

---

## Running the Frontend Client (`client-with-sessions`)

The project includes the official session-based React authentication client provided for this lab.

```bash
# 1. Navigate to the client directory
cd client-with-sessions

# 2. Install dependencies
npm install

# 3. Start the React development server
npm start
```

The frontend serves on **http://localhost:4000** and automatically proxies requests to the Flask backend running on **http://localhost:5555** (`"proxy": "http://localhost:5555"` in `package.json`), ensuring seamless cookie exchange without CORS configuration.

---

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| APP_ENV | development | Set to production to enable Secure cookie and disable debug mode |
| SECRET_KEY | dev-only-secret | Signs the session cookie. Required in production |
| DATABASE_URI | sqlite:///app.db | Overrides the default SQLite database |

### Running the Tests

```bash
pytest -v
```

---

## API Endpoints

### Authentication

| Method | Route | Body | Success | Error |
|---|---|---|---|---|
| POST | /signup | { username, password, password_confirmation? } | 201 user object | 422 validation error |
| POST | /login | { username, password } | 200 user object | 401 bad credentials |
| DELETE | /logout | - | 204 | 401 not logged in |
| GET | /check_session, /me | - | 200 user object | 401 not logged in |

### Notes (login required - owner only)

| Method | Route | Query / Body | Success | Errors |
|---|---|---|---|---|
| GET | /notes | ?page=1&per_page=5 | 200 paginated list | 401 |
| POST | /notes | { title, content } | 201 note object | 401, 422 |
| GET | /notes/<id> | - | 200 note object | 401, 403, 404 |
| PATCH | /notes/<id> | { title?, content? } | 200 updated note | 401, 403, 404, 422 |
| DELETE | /notes/<id> | - | 204 | 401, 403, 404 |

Paginated list response shape:

```json
{
  "page": 1,
  "per_page": 5,
  "total": 12,
  "pages": 3,
  "notes": [ ... ]
}
```

Status code key:

| Code | Meaning |
|---|---|
| 401 | Not logged in |
| 403 | Note belongs to another user |
| 404 | Note not found |
| 422 | Validation error (see errors array in response) |

---

## Project Layout

```
productivity-app-phase5/
|-- README.md                   Primary project documentation
|-- client-with-sessions/       Frontend React client (session-based authentication)
|   |-- package.json            Dependencies and proxy to http://localhost:5555
|   |-- public/                 HTML shell, icons, manifest
|   `-- src/                    React components (SignUpForm, LoginForm, NavBar, App)
|-- productivity-api/           Backend Flask REST API
    |-- app.py                  Entry point - registers routes and runs the server
    |-- config.py               Flask app, database, migrations, bcrypt, API settings
    |-- models.py               User and Note SQLAlchemy models with validation
    |-- schemas.py              Marshmallow schemas for validation and serialization
    |-- utils.py                Login decorator, JSON loader, ownership check, pagination
    |-- seed.py                 Seeds the database with sample users and notes
    |-- Pipfile                 Pinned dependencies
    |-- pytest.ini              Pytest configuration
    |-- migrations/             Alembic migration history
    |-- resources/              Flask-RESTful Resource controllers
    |   |-- __init__.py         Route registration
    |   |-- auth.py             Signup, Login, Logout, CheckSession/Me resources
    |   `-- notes.py            NoteList and NoteDetail resources (full CRUD)
    `-- tests/                  Comprehensive test suite (16 passing tests)
        |-- conftest.py         Pytest fixtures (in-memory SQLite test database)
        `-- test_app.py         Auth and Notes CRUD tests
```

### Key Design Decisions

- **Session-based auth** - Flask signed-cookie session. No JWT dependency needed.
- **Session cleared on login / logout** - guards against session-fixation attacks.
- **Usernames stored lowercase** - lookups are case-insensitive.
- **Marshmallow validates input** - schemas reject unknown fields (EXCLUDE) so
  clients cannot inject user_id into a note.
- **db.session.get()** - uses the SQLAlchemy 2.x primary-key lookup API
  instead of the deprecated Model.query.get().

---

## Validation Rules

| Field | Rule |
|---|---|
| username | 3-50 characters, non-blank, stored lowercase |
| password | 6-128 characters, non-blank |
| title | 1-100 characters, non-blank |
| content | Non-blank string |
