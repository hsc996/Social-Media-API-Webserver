from datetime import date

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from init import db, ma
from models.post import Post, post_schema, posts_schema

posts_bp = Blueprint("posts", __name__, url_prefix="/posts")

# /posts - GET - fetch all posts
# /posts/<id> - GET - fetch a single post
# /posts - POST - create a new post
# /posts/<id> - DELETE - delete a post
# /posts/<id> - PUT, PATCH - edit a post

# /posts - GET - fetch all posts
@posts_bp.route("/")
def get_all_posts():
    stmt = db.select(Post).order_by(Post.timestamp.desc())
    posts = db.session.scalars(stmt)
    return posts_schema.dump(posts)


# /posts/<id> - GET - fetch a single post
@posts_bp.route("/<int:post_id>")
def get_single_post(post_id):
    stmt = db.select(Post).filter_by(id=post_id)
    post = db.session.scalar(stmt)
    if post:
        return post_schema.dump(post)
    else:
        return {"error": f"Post with id {post_id} not found"}, 404


# /posts - POST - create a new post
@posts_bp.route("/", methods=["POST"])
@jwt_required()
def create_post():
    body_data = request.get_json()
    post = Post(
        body=body_data.get("body"),
        timestamp=date.today(),
        user_id=get_jwt_identity()
    )
    db.session.add(post)
    db.session.commit()

    return post_schema.dump(post)


# /posts/<id> - DELETE - delete a post
@posts_bp.route("/<int:post_id>", methods=["DELETE"])
@jwt_required()
def delete_post(post_id):
    stmt = db.select(Post).filter_by(id=post_id)
    post = db.session.scalar(stmt)
    if post:
        db.session.delete(post)
        db.session.commit()

        return {"message":f"Post with ID {post_id} successfully deleted."}
    else:
        return {"error":f"Post with ID {post_id} not found"}, 404


# /posts/<id> - PUT, PATCH - edit a post
@posts_bp.route("/<int:post_id>", methods=["PUT", "PATCH"])
@jwt_required()
def update_post(post_id):
    body_data = request.get_json()
    stmt = db.select(Post).filter_by(id=post_id)
    post = db.session.scalar(stmt)

    if post:
        if str(post.user_id) != get_jwt_identity():
            return {"error": f"Unauthorized to delete: you are not the owner of this post."}, 403
        
        post.body = body_data.get("body") or post.body
        post.timestamp = body_data.get("timestamp") or post.timestamp

        db.session.commit()
        
        return post_schema.dump(post)
    else:
        return {"error":f"Post with ID {post_id} not found."}, 404
    