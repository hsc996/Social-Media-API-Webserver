from datetime import date

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow.exceptions import ValidationError

from init import db, ma
from models.like import Like, like_schema, likes_schema
from models.post import Post, post_schema, posts_schema
from utils import auth_user_action


likes_bp = Blueprint("likes", __name__, url_prefix="/posts/<int:post_id>/likes")


# Get likes for a post - GET - /post/<int:post_id>/likes
@likes_bp.route("/", methods=["GET"])
def get_post_likes(post_id):
    stmt = db.select(Post).filter_by(id=post_id)
    post = db.session.scalar(stmt)

    if post is None:
        return {"error": f"Post with ID {post_id} not found."}, 404
        
    likes = Like.query.filter_by(post_id=post.id).all()
    return likes_schema.dump(likes), 200



# Like a post - POST - /post/<int:post_id>/likes
@likes_bp.route("/", methods=["POST"])
@jwt_required()
def like_post(post_id):
    try:
        user_id = get_jwt_identity()
        stmt = db.select(Post).filter_by(id=post_id)
        post = db.session.scalar(stmt)

        if post is None:
            return {"error": f"Post with ID {post_id} not found."}, 404
        
        if str(post.user_id) == str(user_id):
            return {"error": f"You cannot like your own post."}, 403
        
        existing_like = Like.query.filter_by(user_id=user_id, post_id=post.id).first()
        if existing_like:
            return {"error": f"Post with ID {post_id} already liked."}, 400
        
        new_like = Like(
            user_id=user_id,
            post_id=post.id
        )
        db.session.add(new_like)
        db.session.commit()
        return like_schema.dump(new_like), 201
    
    except ValidationError as e:
        return {"error": str(e)}, 400
    
    except Exception as e:
        db.session.rollback()
        return {"error": "Internal Server Error"}, 500


# Unlike a post - DELETE - /post/<int:post_id>/likes/<int:like_id>
@likes_bp.route("/<int:like_id>", methods=["DELETE"])
@jwt_required()
@auth_user_action(Like, "like_id")
def unlike_post(post_id, like_id):
    try:
        user_id = get_jwt_identity()
        stmt = db.select(Post).filter_by(id=post_id)
        post = db.session.scalar(stmt)

        if post is None:
            return {"error": f"Post with ID {post_id} not found"}, 404
        
        existing_like = Like.query.filter_by(user_id=user_id, post_id=post.id).first()
        if not existing_like:
            return {"error": "Like not found"}, 404
        
        # is_authorised, auth_error = auth_user_action(user_id, Like, existing_like.id)
        # if not is_authorised:
        #     return {"error": auth_error["error_code"], "message": auth_error["message"]}, 403
        
        db.session.delete(existing_like)
        db.session.commit()
        return {"message": "Like removed"}, 200
        
    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 500
