from datetime import date

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from init import db
from models.comment import Comment, comment_schema, comments_schema
from models.post import Post, post_schema, posts_schema
from utils import auth_user_action


comments_bp = Blueprint("comments", __name__, url_prefix="/<int:post_id>/comments")


# Create comment - POST - /<int:post_id>/comments
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
            posts=post,
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
def delete_comment(post_id, comment_id):
    try:
        user_id = get_jwt_identity()
        stmt = db.select(Comment).filter_by(id=comment_id)
        comment = db.session.scalar(stmt)

        if comment is None:
            return {"error": f"Comment with ID '{comment_id}' not found"}, 404

        is_authorised, auth_error = auth_user_action(user_id, Comment, comment_id)
        if not is_authorised:
            return {"error": auth_error["error_code"], "message": auth_error["message"]}, 403
        
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
def edit_comment(post_id, comment_id):
    try:
        user_id = get_jwt_identity()
        body_data = request.get_json()
        stmt = db.select(Comment).filter_by(id=comment_id)
        comment = db.session.scalar(stmt)

        if comment is None:
            return {"error": f"Comment with ID '{comment_id}' not found"}, 404
        
        is_authorised, auth_error = auth_user_action(user_id, Comment, comment_id)
        if not is_authorised:
            return {"error": auth_error["error_code"], "message": auth_error["message"]}, 403
        
        if comment.post_id != post_id:
            return {"error": f"Comment with ID '{comment_id}' does not belong to Post with ID {post_id}"}, 404
        
        comment.comment_body = body_data.get("comment_body") or comment.comment_body
        db.session.commit()
        return comment_schema.dump(comment), 200
    
    except ValidationError as e:
        return {"error": str(e)}, 400
    
    except Exception as e:
        return {"error": "Internal Server Error"}, 500
    

