from flask import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow.exceptions import ValidationError

from init import db
from models.like import Like, like_schema, likes_schema
from models.post import Post
from utils import auth_like_action


likes_bp = Blueprint("likes", __name__, url_prefix="/posts/<int:post_id>/likes")


# Fetch all likes on a post - GET - /post/<int:post_id>/likes
@likes_bp.route("/", methods=["GET"])
def get_post_likes(post_id):
    """
    Fetch all likes on a specific post.

    Args:
        post_id (int): The ID of the post.

    Returns:
        JSON: Serialised likes with 200 OK status if successful.
        JSON: Error message with a 404 Not Found status if the post is not found.
    """
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
    """
    Like a speicifc post.

    Users can like a post they do not own. Prevents liking a post more than once.

    Args:
        post_id (int): The ID of the post to like.

    Returns:
        JSON: Serialised like with a 201 Created status if successful.
        JSON: Error message with a 404 Not Found status if the post is not found.
        JSON: Error message with a 403 Forbidden status if the user attempts to like their own post.
    """
    try:
        user_id = get_jwt_identity()
        stmt = db.select(Post).filter_by(id=post_id)
        post = db.session.scalar(stmt)

        if not post:
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
@auth_like_action
def unlike_post(post_id, like_id):
    """
    Removes a like from a specific post.

    Args:
        post_id (int): The ID of the post.
        like_id (int): The Id of the like to remove.

    Returns:
        JSON: Success message with a 200 OK status if like is successful.
        JSON: Error message with a 404 Not Found status if the like is not found.
    """
    try:
        user_id = get_jwt_identity()
        stmt = db.select(Post).filter_by(id=post_id)
        post = db.session.scalar(stmt)

        if post is None:
            return {"error": f"Post with ID {post_id} not found"}, 404
        
        existing_like = Like.query.filter_by(user_id=user_id, post_id=post.id).first()
        if not existing_like:
            return {"error": "Like not found"}, 404
        
        db.session.delete(existing_like)
        db.session.commit()
        return {"message": "Like removed"}, 200
        
    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 500
