from config import ENV, app
from resources import register_routes

register_routes()

if __name__ == "__main__":
    app.run(port=5555, debug=ENV == "development")
