import os
from flask import Flask
from init import db, ma, bcrypt, jwt


def create_app():
    app = Flask(__name__)

    app.json.sort_keys = False

    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")

    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY")

    db.init_app(app)
    ma.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    from controllers.cli_controllers import db_commands
    app.register_blueprint(db_commands)

    from controllers.post_controller import posts_bp
    app.register_blueprint(posts_bp)

    from controllers.like_controller import likes_bp
    app.register_blueprint(likes_bp)

    from controllers.comment_controller import comments_bp
    app.register_blueprint(comments_bp)

    # from controllers.like_controller import follower_bp
    # app.register_blueprint(follower_bp)

    from controllers.auth_controller import auth_bp
    app.register_blueprint(auth_bp)


    return app