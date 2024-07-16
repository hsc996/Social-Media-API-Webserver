from datetime import date

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.orm.exc import NoResultFound
from marshmallow import ValidationError

from init import db, ma
from models.post import Post, post_schema, posts_schema
from controllers.comment_controller import comments_bp
from utils import authorise_as_admin

posts_bp = Blueprint("posts", __name__, url_prefix="/posts")
posts_bp.register_blueprint(comments_bp)



# /posts - GET - fetch all posts
@posts_bp.route("/")
def get_all_posts():
    stmt = db.select(Post).order_by(Post.timestamp.desc())
    posts = db.session.scalars(stmt)
    return posts_schema.dump(posts)


# /posts/<id> - GET - fetch a single post
@posts_bp.route("/<int:post_id>")
def get_single_post(post_id):
    try:
        stmt = db.select(Post).filter_by(id=post_id)
        post = db.session.scalar(stmt)
        return post_schema.dump(post)
    except NoResultFound:
        return {"error": f"Post with id {post_id} not found"}, 404


# /posts - POST - create a new post
@posts_bp.route("/", methods=["POST"])
@jwt_required()
def create_post():
    try:
        body_data = request.get_json()

        if not body_data or not body_data.get("body"):
            return {"error": "Invalid request body"}, 400
        
        post = Post(
            body=body_data.get("body"),
            timestamp=date.today(),
            user_id=get_jwt_identity()
        )
        db.session.add(post)
        db.session.commit()

        return post_schema.dump(post)
    
    except ValidationError as e:
        return {"error": str(e)}, 400
    
    except Exception as e:
        db.session.rollback()
        return {"error": "Internal Server Error"}, 500



# /posts/<id> - DELETE - delete a post
@posts_bp.route("/<int:post_id>", methods=["DELETE"])
@jwt_required()
def delete_post(post_id):
    try:
        stmt = db.select(Post).filter_by(id=post_id)
        post = db.session.scalar(stmt)

        is_admin = authorise_as_admin()
        if not is_admin or str(post.user_id) != get_jwt_identity():
            return {"error": f"Unauthorized to delete: you are not the owner of this post."}, 403
        
        db.session.delete(post)
        db.session.commit()

        return {"message":f"Post with ID {post_id} successfully deleted."}
    
    except NoResultFound:
        return {"error":f"Post with ID {post_id} not found"}, 404
    
    except Exception as e:
        db.session.rollback()
        return {"error": "Internal Server Error"}, 500
    


# /posts/<id> - PUT, PATCH - edit a post
@posts_bp.route("/<int:post_id>", methods=["PUT", "PATCH"])
@jwt_required()
def update_post(post_id):
    try:
        body_data = request.get_json()
        stmt = db.select(Post).filter_by(id=post_id)
        post = db.session.scalar(stmt)

        is_admin = authorise_as_admin()
        if not is_admin or str(post.user_id) != get_jwt_identity():
            return {"error": f"Unauthorized to delete: you are not the owner of this post."}, 403
        
        post.body = body_data.get("body") or post.body
        post.timestamp = body_data.get("timestamp") or post.timestamp

        db.session.commit()
        
        return post_schema.dump(post)
    
    except ValidationError as e:
        return {"error": str(e)}, 400

    except NoResultFound:
        return {"error":f"Post with ID {post_id} not found."}, 404
    
    except Exception as e:
        return {"error": "Internal Server Error"}, 500
    