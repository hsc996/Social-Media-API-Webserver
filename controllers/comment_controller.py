from datetime import date

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from init import db
from models.comment import Comment, comment_schema, comments_schema
from models.post import Post, post_schema, posts_schema


comments_bp = Blueprint("comments", __name__, url_prefix="/<int:post_id>/comments")

# Create comment route - POST - /post_id/comments
@comments_bp.route("/", methods=["POST"])
@jwt_required()
def create_comment(post_id):
    body_data = request.get_json()
    stmt = db.select(Post).filter_by(id=post_id)
    post = db.session.scalar(stmt)

    if post:
        comment = Comment(
            comment_body=body_data.get("comment_body"),
            timestamp=date.today(),
            posts=post,
            user_id=get_jwt_identity()
        )
        db.session.add(comment)
        db.session.commit()

        return comment_schema.dump(comment)
    else:
        return {"error":f"Post with ID {post_id} not found."}, 404


# Delete Comment - /posts/post_id/comments/comment_id
@comments_bp.route("/<int:comment_id>", methods=["DELETE"])
@jwt_required()
def delete_comment(post_id, comment_id):
    stmt = db.select(Comment).filter_by(id=comment_id)
    comment = db.session.scalar(stmt)
    if comment:
        db.session.delete(comment)
        db.session.commit()
        return {"message": f"Comment with ID '{comment_id}' deleted successfully"}
    else:
        return {"error": f"Comment with ID {comment_id} not found"}, 404