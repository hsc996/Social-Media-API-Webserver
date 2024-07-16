from datetime import date

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from init import db, ma
from models.post import Post, post_schema, posts_schema
from controllers.comment_controller import comments_bp
from utils import authorise_as_admin

posts_bp = Blueprint("posts", __name__, url_prefix="/posts")
posts_bp.register_blueprint(comments_bp)



# Fetch all posts - GET - /posts
@posts_bp.route("/")
def get_all_posts():
    stmt = db.select(Post).order_by(Post.timestamp.desc())
    posts = db.session.scalars(stmt)
    return posts_schema.dump(posts), 200


# Fetch a single post - GET - /posts/<int:post_id>
@posts_bp.route("/<int:post_id>")
def get_single_post(post_id):
    stmt = db.select(Post).filter_by(id=post_id)
    post = db.session.scalar(stmt)
    if post is None:
        return {"error": f"Post with ID {post_id} not found."}, 404
    return post_schema.dump(post), 200


# Create a post - POST - /posts
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

        return post_schema.dump(post), 201
    
    except ValidationError as e:
        return {"error": str(e)}, 400
    
    except Exception as e:
        db.session.rollback()
        return {"error": "Internal Server Error"}, 500



# Delete a post - DELETE - /posts/<int:post_id>
@posts_bp.route("/<int:post_id>", methods=["DELETE"])
@jwt_required()
def delete_post(post_id):
    try:
        stmt = db.select(Post).filter_by(id=post_id)
        post = db.session.scalar(stmt)

        if post is None:
            return {"error":f"Post with ID {post_id} not found"}, 404

        is_admin = authorise_as_admin()
        if not is_admin and str(post.user_id) != get_jwt_identity():
            return {"error": f"Unauthorized to delete: you are not the owner of this post."}, 403
        
        db.session.delete(post)
        db.session.commit()

        return {"message":f"Post with ID {post_id} successfully deleted."}, 200
    
    except Exception as e:
        db.session.rollback()
        return {"error": "Internal Server Error"}, 500
    


# Edit a post - PUT, PATCH - /posts/<int:post_id>
@posts_bp.route("/<int:post_id>", methods=["PUT", "PATCH"])
@jwt_required()
def update_post(post_id):
    try:
        body_data = request.get_json()
        stmt = db.select(Post).filter_by(id=post_id)
        post = db.session.scalar(stmt)

        if post is None:
            return {"error": f"Post with ID {post_id} not found."}, 404

        is_admin = authorise_as_admin()
        if not is_admin and str(post.user_id) != get_jwt_identity():
            return {"error": f"Unauthorized to edit: you are not the owner of this post."}, 403
        
        post.body = body_data.get("body") or post.body
        post.timestamp = body_data.get("timestamp") or post.timestamp

        db.session.commit()
        
        return post_schema.dump(post), 200
    
    except ValidationError as e:
        return {"error": str(e)}, 400
    
    except Exception as e:
        db.session.rollback()
        return {"error": "Internal Server Error"}, 500
    