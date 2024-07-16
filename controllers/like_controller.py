from datetime import date

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from init import db, ma
from models.like import Like, like_schema, likes_schema
from models.post import Post, post_schema, posts_schema


likes_bp = Blueprint("likes", __name__, url_prefix="/posts/<int:post_id>/likes")


# Get likes for a post - GET - /post/post_id/likes
@likes_bp.route("/", methods=["GET"])
def get_post_likes(post_id):
    stmt = db.select(Post).filter_by(id=post_id)
    post = db.session.scalar(stmt)

    if post:
        likes = Like.query.filter_by(post_id=post.id).all()
        return likes_schema.dump(likes), 200
    else:
        return {"error": f"Post with ID {post_id} not found."}, 404



# Like a post - POST - /posts/post_id/likes
@likes_bp.route("/", methods=["POST"])
@jwt_required()
def like_post(post_id):
    user_id = get_jwt_identity()
    stmt = db.select(Post).filter_by(id=post_id)
    post = db.session.scalar(stmt)

    if post:
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
    else:
        return {"error": f"Post with ID {post_id} not found."}, 404



# Unlike a post - DELETE - /post/post_id/likes
@likes_bp.route("/", methods=["DELETE"])
@jwt_required()
def unlike_post(post_id):
    user_id = get_jwt_identity()
    stmt = db.select(Post).filter_by(id=post_id)
    post = db.session.scalar(stmt)

    if post:
        existing_like = Like.query.filter_by(user_id=user_id, post_id=post.id).first()
        if not existing_like:
            return {"error": "Like not found"}, 404
        
        db.session.delete(existing_like)
        db.session.commit()
        return {"message": "Like removed"}, 200
    else:
        return {"error": f"Post with ID {post_id} not found"}, 404
