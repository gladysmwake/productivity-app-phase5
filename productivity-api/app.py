"""Application entry point for the Productivity Notes API.

Run from this directory with:  python app.py
"""
from config import ENV, app
from resources import register_routes

# Attach all Flask-RESTful Resource classes to their URL routes
register_routes()

if __name__ == "__main__":
    app.run(port=5555, debug=ENV == "development")
