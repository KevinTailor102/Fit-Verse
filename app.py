"""
FitVerse — Main Flask Application Entry Point
"""
import os
from datetime import datetime
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from dotenv import load_dotenv

from config import config_map
from models import db, bcrypt, User

load_dotenv()


def create_app(config_name: str = None) -> Flask:
    """Application factory."""
    app = Flask(__name__)

    # Load config
    env = config_name or os.environ.get("FLASK_ENV", "development")
    app.config.from_object(config_map.get(env, config_map["default"]))

    # Extensions
    db.init_app(app)
    bcrypt.init_app(app)
    Migrate(app, db)

    # Flask-Login
    login_manager = LoginManager(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access FitVerse. 🏋️"
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Blueprints
    from routes.main import main_bp
    from routes.auth import auth_bp
    from routes.chat import chat_bp
    from routes.fitness import fitness_bp
    from routes.nutrition import nutrition_bp
    from routes.tracker import tracker_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(fitness_bp)
    app.register_blueprint(nutrition_bp)
    app.register_blueprint(tracker_bp)

    # Jinja2 globals
    app.jinja_env.globals['now'] = datetime.utcnow

    # Create DB tables on first run
    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
