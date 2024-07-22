from datetime import datetime, date

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow.exceptions import ValidationError

from src.init import db
from src.models.post import Post, post_schema, posts_schema
from src.models.like import Like
from src.models.comment import Comment
from src.models.thread import InnovationThread
from src.controllers.comment_controller import comments_bp
from src.utils import auth_user_action


posts_bp = Blueprint("posts", __name__, url_prefix="/posts")
posts_bp.register_blueprint(comments_bp)


# POST CONTROLLERS ALLOWING USERS TO POST FROM THEIR ACCOUNT


# Fetch all posts - GET - /posts
@posts_bp.route("/", methods=["GET"])
def get_all_posts():
    stmt = db.select(Post).order_by(Post.timestamp.desc())
    posts = db.session.scalars(stmt)
    return posts_schema.dump(posts), 200


# Fetch a single post - GET - /posts/<int:post_id>
@posts_bp.route("/<int:post_id>", methods=["GET"])
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
        body_data = post_schema.load(request.get_json())

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
        
        db.session.query(Like).filter_by(post_id=post_id).delete()
        db.session.query(Comment).filter_by(post_id=post_id).delete()

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
        body_data = post_schema.load(request.get_json(), partial=True)
        stmt = db.select(Post).filter_by(id=post_id)
        post = db.session.scalar(stmt)

        if not post:
            return {"error": f"Post with ID {post_id} not found."}, 404

        post.body = body_data.get("body", post.body)
        if body_data.get("timestamp"):
            post.timestamp = datetime.strptime(body_data["timestamp"], "%Y-%m-%d").date()

        db.session.commit()
        
        return post_schema.dump(post), 200
    
    except ValidationError as e:
        return {"error": e.messages}, 400
    
    except Exception as e:
        db.session.rollback()
        return {"error": "Internal Server Error"}, 500
    



# POST CONTROLLERS THAT ALLOW USERS TO POST WITHIN EXISTING INNOVATION THREADS



# Get all posts on a specific thread - GET - /posts/threads/<int:thread_id>
@posts_bp.route("threads/<int:thread_id>", methods=["GET"])
def get_all_posts_in_thread(thread_id):
    try:
        stmt = db.select(Post).filter_by(thread_id=thread_id).order_by(Post.timestamp.desc())
        posts = db.session.scalars(stmt).all()

        if not posts:
            return {"error": f"No posts found in Thread with ID {thread_id}."}, 404
        
        return posts_schema.dump(posts), 200
    
    except Exception as e:
        print(f"Error: {e}")
        return {"error": "Internal Server Error."}, 500
    


# Get a specfic post on a specific thread - GET - /posts/<int:post_id>/threads/<int:thread_id>
@posts_bp.route("<int:post_id>/threads/<int:thread_id>", methods=["GET"])
def get_posts_in_thread(thread_id, post_id):
    try:
        stmt = db.select(Post).filter_by(id=post_id, thread_id=thread_id)
        post = db.session.scalar(stmt)

        if not post:
            return {"error": f"Post with ID {post_id} not found in Thread with ID {thread_id}."}, 404
        
        return post_schema.dump(post), 200
    
    except Exception as e:
        return {"error": "Internal Server Error."}, 500
    


# Post to a specific thread - POST - /posts/threads/<int:thread_id>
@posts_bp.route("/threads/<int:thread_id>", methods=["POST"])
@jwt_required()
def post_to_thread(thread_id):
        try:
            body_data = post_schema.load(request.get_json())

            if not body_data or not isinstance(body_data["body"], str) or not body_data.get("body").strip():
                return {"error": "Invalid request body"}, 400
            
            stmt = db.select(InnovationThread).filter_by(id=thread_id)
            thread = db.session.scalar(stmt)

            if thread is None:
                return {"error": f"Thread with ID {thread_id} not found."}, 404
            
            new_post = Post(
                body=body_data.get("body"),
                timestamp=date.today(),
                user_id=get_jwt_identity(),
                thread_id=thread_id
            )
            db.session.add(new_post)
            db.session.commit()

            return {"message": "Post created successfully", "post_id": new_post.id}, 201
        
        except ValidationError as e:
            return {"error": str(e)}, 400
    
        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": "Internal Server Error"}, 500



# Edit post on a thread - EDIT - /post/<int:post_id>/threads/<int:thread_id>
@posts_bp.route("/<int:post_id>/threads/<int:thread_id>", methods=["PUT", "PATCH"])
@jwt_required()
@auth_user_action(Post, "post_id")
def update_post_in_thread(thread_id, post_id):
    try:
        body_data = post_schema.load(request.get_json(), partial=True)
        stmt = db.select(Post).filter_by(id=post_id, thread_id=thread_id)
        post = db.session.scalar(stmt)

        if not post:
            return {"error": f"Post with ID {post_id} not found in Thread with ID {thread_id}."}, 404
        
        post.body = body_data.get("body", post.body)
        if body_data.get("timestamp"):
            post.timestamp = datetime.strptime(body_data["timestamp"], "%Y-%m-%d").date()
        
        db.session.commit()

        return post_schema.dump(post), 200
    
    except ValidationError as e:
        return {"error": e.messages}, 400
    
    except Exception as e:
        db.session.rollback()
        return {"error": "Internal Server Error."}, 500
    


# Delete post in thread - DELETE - /post/<int:post_id>/threads/<int:thread_id>
@posts_bp.route("/<int:post_id>/threads/<int:thread_id>", methods=["DELETE"])
@jwt_required()
@auth_user_action(Post, "post_id")
def delete_post_in_thread(thread_id, post_id):
    try:
        stmt = db.select(Post).filter_by(id=post_id, thread_id=thread_id)
        post = db.session.scalar(stmt)

        if not post:
            return {"error": f"Post with ID {post_id} not found in Thread with ID {thread_id}."}, 404
        
        db.session.query(Like).filter_by(post_id=post_id).delete()
        db.session.query(Comment).filter_by(post_id=post_id).delete()

        db.session.delete(post)
        db.session.commit()

        return {"message": f"Post with ID {post_id} deleted successfully."}, 200
    
    except Exception as e:
        db.session.rollback()
        print(e)
        return {"error": "Internal Server Error."}, 500