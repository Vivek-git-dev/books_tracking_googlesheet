import os
from flask import Flask

# load environment variables from a .env file before importing config
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from config import Config
from extensions import login_manager
from models import load_user

def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)

    # ensure the instance folder exists (used for local credentials file, etc.)
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    app.config.from_object(config_class)

    # Initialize Flask extensions
    login_manager.init_app(app)
    login_manager.user_loader(load_user)

    # Register Blueprints
    from auth.routes import auth_bp
    from main.routes import main_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    return app

if __name__ == "__main__":
    app = create_app()
    # use env vars for host/port in case a platform provides them
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    app.run(host=host, port=port, debug=False)
