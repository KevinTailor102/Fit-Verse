"""
FitVerse — Main Flask Application Entry Point
"""
import os
import warnings
from datetime import datetime
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from dotenv import load_dotenv

# Load .env with override=True so real values always win,
# even when Flask debug reloader restarts the process
load_dotenv(override=True)

# Silence noisy IBM SDK warnings globally
warnings.filterwarnings("ignore", message=".*WatsonxAPIWarning.*")
warnings.filterwarnings("ignore", module="ibm_watsonx_ai")

from config import config_map
from models import db, bcrypt, User


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

    # ── Pre-initialise watsonx.ai client so it's ready on first request ──
    # Reset first so Flask reloader always picks up the latest .env values
    from watsonx_client import reset_client, get_watsonx_client
    reset_client()
    client = get_watsonx_client()
    if client:
        app.logger.info("✅ FitVerse AI Coach is ONLINE — model: %s", client.model_id)
    else:
        app.logger.warning("⚠️  FitVerse AI Coach is OFFLINE — check .env credentials")

    return app


app = create_app()

if __name__ == "__main__":
    port  = int(os.environ.get("PORT", 5000))
    # Run with use_reloader=False to prevent the double-init problem in debug mode
    # The app still hot-reloads templates/static; only Python restarts are suppressed
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug, use_reloader=False)
