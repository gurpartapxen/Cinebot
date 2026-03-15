from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from config import Config

db            = SQLAlchemy()
login_manager = LoginManager()
bcrypt        = Bcrypt()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.routes.auth      import auth
    from app.routes.chat      import chat
    from app.routes.profile   import profile_bp
    from app.routes.discover  import discover_bp
    from app.routes.social    import social_bp
    from app.routes.streaming import streaming_bp

    app.register_blueprint(auth)
    app.register_blueprint(chat)
    app.register_blueprint(profile_bp)
    app.register_blueprint(discover_bp)
    app.register_blueprint(social_bp)
    app.register_blueprint(streaming_bp)

    return app