from dotenv import load_dotenv
import os
from flask import Flask
from src.init import db, ma, bcrypt, jwt


def create_app():
    app = Flask(__name__)

    app.json.sort_keys = False

    load_dotenv()

    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")

    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY")

    db.init_app(app)
    ma.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    from src.controllers.cli_controllers import db_commands
    app.register_blueprint(db_commands)

    from src.controllers.post_controller import posts_bp
    app.register_blueprint(posts_bp)

    from src.controllers.like_controller import likes_bp
    app.register_blueprint(likes_bp)

    from src.controllers.comment_controller import comments_bp
    app.register_blueprint(comments_bp)

    from src.controllers.thread_controller import thread_bp
    app.register_blueprint(thread_bp)

    from src.controllers.follower_controller import follower_bp
    app.register_blueprint(follower_bp)

    from src.controllers.auth_controller import auth_bp
    app.register_blueprint(auth_bp)


    return app