from datetime import date

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow.exceptions import ValidationError
import traceback

from init import db
from models.comment import Comment, comment_schema, comments_schema
from models.post import Post
from utils import auth_user_action


comments_bp = Blueprint("comments", __name__, url_prefix="/posts/<int:post_id>/comments")


# Fetch all comments - GET - /posts/<int:post_id>/comments
@comments_bp.route("/", methods=["GET"])
def get_all_comments(post_id):
    try:
        post_stmt = db.select(Post).filter_by(id=post_id)
        post = db.session.scalar(post_stmt)

        if not post:
            return {"error": f"Post with ID '{post_id}' not found."}, 404
        
        stmt = db.select(Comment).filter_by(post_id=post_id).order_by(Comment.timestamp.desc())
        comments = db.session.scalars(stmt).all()

        return comments_schema.dump(comments), 200
    
    except Exception as e:
        db.session.rollback()
        return {"error": "Internal Server Error"}, 500
    


# Fetch one particular comment - GET - /posts/<int:post_id>/comments/<int:comment_id>
@comments_bp.route("/<int:comment_id>", methods=["GET"])
def get_single_comment(post_id, comment_id):
    try:
        post = Post.query.get(post_id)
        if not post:
            return {"error": f"Post with ID '{post_id}' not found."}, 404
        
        comment = Comment.query.filter_by(id=comment_id, post_id=post_id).first()

        if not comment:
            return {"error": f"Comment with ID {comment_id} not found for Post with ID {post_id}"}, 404

        return comment_schema.dump(comment), 200
    
    except Exception as e:
        db.session.rollback()
        return {"error": "Internal Server Error"}, 500
        


# Create comment - POST - /posts/<int:post_id>/comments
@comments_bp.route("/", methods=["POST"])
@jwt_required()
def create_comment(post_id):
    try:
        body_data = request.get_json()
        stmt = db.select(Post).filter_by(id=post_id)
        post = db.session.scalar(stmt)

        if post is None:
            return {"error": f"Post with ID '{post_id}' not found."}, 404
        
        comment = Comment(
            comment_body=body_data.get("comment_body"),
            timestamp=date.today(),
            post_id=post.id,
            user_id=get_jwt_identity()
        )
        db.session.add(comment)
        db.session.commit()

        return comment_schema.dump(comment), 201
    
    except ValidationError as e:
        return {"error": str(e)}, 400
    
    except Exception as e:
        db.session.rollback()
        return {"error": "Internal Server Error"}, 500


# Delete Comment - DELETE - /posts/<int:post_id>/comments/<int:comment_id>
@comments_bp.route("/<int:comment_id>", methods=["DELETE"])
@jwt_required()
@auth_user_action(Comment, "comment_id")
def delete_comment(post_id, comment_id):
    try:
        post_stmt = db.select(Post).filter_by(id=post_id)
        post = db.session.scalar(post_stmt)

        if not post:
            return {"error": f"Post with ID {post_id} not found."}, 404
        
        user_id = get_jwt_identity()
        stmt = db.select(Comment).filter_by(id=comment_id)
        comment = db.session.scalar(stmt)

        if not comment:
            return {"error": f"Comment with ID '{comment_id}' not found"}, 404
        
        if comment.post_id != post_id:
            return {"error": f"Comment with ID '{comment_id}' does not belong to Post with ID {post_id}"}, 404
        
        db.session.delete(comment)
        db.session.commit()

        return {"message": f"Comment with ID '{comment_id}' deleted successfully"}, 200
    
    except Exception as e:
        db.session.rollback()
        return {"error": "Internal Server Error"}, 500


# Update comment - PUT, PATCH - /posts/<int:post_id>/comments/<int:comment_id>
@comments_bp.route("/<int:comment_id>", methods=["PUT", "PATCH"])
@jwt_required()
@auth_user_action(Comment, "comment_id")
def edit_comment(post_id, comment_id):
    try:
        post_stmt = db.select(Post).filter_by(id=post_id)
        post = db.session.scalar(post_stmt)

        if not post:
            return {"error": f"Post with ID {post_id} not found."}, 404
        
        user_id = get_jwt_identity()
        body_data = request.get_json()
        stmt = db.select(Comment).filter_by(id=comment_id)
        comment = db.session.scalar(stmt)

        if not comment:
            return {"error": f"Comment with ID '{comment_id}' not found"}, 404
        
        if comment.post_id != post_id:
            return {"error": f"Comment with ID '{comment_id}' does not belong to Post with ID {post_id}"}, 404
        
        comment.comment_body = body_data.get("comment_body") or comment.comment_body
        db.session.commit()
        return comment_schema.dump(comment), 200
    
    except ValidationError as e:
        return {"error": str(e)}, 400
    
    except Exception as e:
        return {"error": "Internal Server Error"}, 500
    

