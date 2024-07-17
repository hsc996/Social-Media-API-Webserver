from datetime import datetime, date

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow.exceptions import ValidationError

from init import db
from models.post import Post, post_schema, posts_schema
from models.like import Like
from models.comment import Comment
from controllers.comment_controller import comments_bp
from utils import auth_user_action


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

        if not body_data or not isinstance(body_data["body"], str) or not body_data.get("body").strip():
            return {"error": "Invalid request body"}, 400
        
        new_post = Post(
            body=body_data.get("body"),
            timestamp=date.today(),
            user_id=get_jwt_identity()
        )
        db.session.add(new_post)
        db.session.commit()

        return {"message": "Post created successfully", "post_id": new_post.id}, 201
    
    except ValidationError as e:
        return {"error": str(e)}, 400
    
    except Exception as e:
        db.session.rollback()
        return {"error": "Internal Server Error"}, 500



# Delete a post - DELETE - /posts/<int:post_id>
@posts_bp.route("/<int:post_id>", methods=["DELETE"])
@jwt_required()
@auth_user_action(Post, "post_id")
def delete_post(post_id):
    try:
        post = Post.query.get(post_id)
        
        if not post:
            return {"error": f"Post with ID {post_id} not found."}, 404
        
        likes = Like.query.filter_by(post_id=post_id).all()
        for like in likes:
            db.session.delete(like)

        comments = Comment.query.filter_by(post_id=post_id).all()
        for comment in comments:
            db.session.delete(comment)

        db.session.delete(post)
        db.session.commit()

        return {"message": f"Post with ID {post_id} successfully deleted."}, 200
    
    except Exception as e:
        db.session.rollback()
        print(e)
        return {"error": "Internal Server Error"}, 500
    


# Edit a post - PUT, PATCH - /posts/<int:post_id>
@posts_bp.route("/<int:post_id>", methods=["PUT", "PATCH"])
@jwt_required()
@auth_user_action(Post, "post_id")
def update_post(post_id):
    try:
        user_id = get_jwt_identity()
        body_data = request.get_json()
        stmt = db.select(Post).filter_by(id=post_id)
        post = db.session.scalar(stmt)
        
        post.body = body_data.get("body") or post.body
        if body_data.get("timestamp"):
            post.timestamp = datetime.strptime(body_data["timestamp"], "%Y-%m-%d").date()

        db.session.commit()
        
        return post_schema.dump(post), 200
    
    except ValidationError as e:
        return {"error": str(e)}, 400
    
    except Exception as e:
        db.session.rollback()
        return {"error": "Internal Server Error"}, 500
    