from datetime import date

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow.exceptions import ValidationError

from init import db
from models.comment import Comment, comment_schema, comments_schema
from models.post import Post
from utils import auth_comment_action, get_comment, get_post


comments_bp = Blueprint("comments", __name__, url_prefix="/posts/<int:post_id>/comments")



# Fetch all comments - GET - /posts/<int:post_id>/comments
@comments_bp.route("/", methods=["GET"])
def get_all_comments(post_id):
    """
    Retrieves all the comments for a given post.

    Queries the database for comments associated with a specific post ID and returns them ordered by timestamp.

    Args:
        post_id (int): The ID of the post for which to retrieve the comments.
    
    Returns:
        JSON: Serialised comments with a 200 OK status if comments exist.
        JSON: Error message with a 404 Not Found status if the post is not found.
    """
    try:
        post = get_post(post_id)
        if not post:
            return {"error": f"Post with ID '{post_id}' not found."}, 404
        
        stmt = db.select(Comment).filter_by(post_id=post_id).order_by(Comment.timestamp.desc())
        comments = db.session.scalars(stmt).all()

        if not comments:
            return {"message": "There are no comments that belong to this post yet."}, 200

        return comments_schema.dump(comments), 200
    
    except Exception as e:
        db.session.rollback()
        return {"error": "Internal Server Error"}, 500
    


# Fetch one particular comment - GET - /posts/<int:post_id>/comments/<int:comment_id>
@comments_bp.route("/<int:comment_id>", methods=["GET"])
def get_single_comment(post_id, comment_id):
    """
    Retrieves a single comment by its ID for a given post.

    Args:
        post_id (int): The ID of the post.
        comment_id (int): The ID of the comment to retrieve.

    Returns:
        JSON: Serialised comment with a 200 OK status if comment is found.
        JSON: Error message with a 404 Not Found status if the comment is not found.
    """
    try:
        post = get_post(post_id)
        if not post:
            return {"error": f"Post with ID '{post_id}' not found."}, 404
        
        comment = get_comment(comment_id, post_id)
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
    """
    Create a new comment on a given post.

    Validates and creates a comment associated with a specified post ID.

    Args:
        post_id (int): The ID of the post to comment on.

    Returns:
        JSON: Serialised comment with a 201 Created status if creation is successful.
        JSON: Error message with a 400 Bad Request status if validation fails.
    """
    try:
        post = get_post(post_id)
        if not post:
            return {"error": f"Post with ID '{post_id}' not found."}, 404
        
        body_data = request.get_json()
        comment_body = body_data.get("comment_body", "").strip()

        if not comment_body or len(comment_body) > 200:
            return {"error": "Comment body must be between 1 and 200 characters and cannot be empty."}, 400
        
        comment = Comment(
            comment_body=comment_body,
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
        print(e)
        return {"error": "Internal Server Error"}, 500



# Update comment - PUT, PATCH - /posts/<int:post_id>/comments/<int:comment_id>
@comments_bp.route("/<int:comment_id>", methods=["PUT", "PATCH"])
@jwt_required()
@auth_comment_action
def edit_comment(post_id, comment_id):
    """
    Updates an existing comment by its ID foe a given post.

    Args:
        post_id (int): The ID of the post.
        comment_id (int): The ID of the comment to update.

    Returns:
        JSON: Serialised comment with a 200 OK status if update is successful.
        JSON: Error message with a 404 Not Found status if the post or comment is not found.
        JSON: Error message with a 400 Bad Request status if validation fails.
    """
    try:
        post = get_post(post_id)
        if not post:
            return {"error": f"Post with ID {post_id} not found."}, 404
        
        comment = get_comment(comment_id, post_id)
        if not comment:
            return {"error": f"Comment with ID '{comment_id}' not found"}, 404
        
        if comment.post_id != post_id:
            return {"error": f"Comment with ID '{comment_id}' does not belong to Post with ID {post_id}"}, 404
        
        body_data = request.get_json()
        comment_body = body_data.get("comment_body", "").strip()

        if not comment_body or len(comment_body) > 200:
            return {"error": "Comment body must be between 1 and 200 characters and cannot be empty."}, 400
        
        comment.comment_body = comment_body or comment.comment_body
        db.session.commit()
        return comment_schema.dump(comment), 200
    
    except ValidationError as e:
        return {"error": str(e)}, 400
    
    except Exception as e:
        return {"error": "Internal Server Error"}, 500
    



# Delete Comment - DELETE - /posts/<int:post_id>/comments/<int:comment_id>
@comments_bp.route("/<int:comment_id>", methods=["DELETE"])
@jwt_required()
@auth_comment_action
def delete_comment(post_id, comment_id):
    """
    Deleted a comment by its ID for a given post.

    Args:
        post_id (int): The ID of the post.
        comment_id (int): The ID of the comment to delete.

    Returns:
        JSON: Success message with a 200 OK status if deleted is successful.
        JSON: Error message with a 404 Not Found status if the post or comment is not found.
    """
    try:
        post = get_post(post_id)
        if not post:
            return {"error": f"Post with ID {post_id} not found."}, 404
        
        comment = get_comment(comment_id, post_id)
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

    




