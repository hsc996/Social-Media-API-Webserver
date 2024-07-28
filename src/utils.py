from functools import wraps
from flask_jwt_extended import get_jwt_identity
from sqlalchemy.orm.exc import NoResultFound
from psycopg2 import errorcodes

from init import db
from models.user import User
from models.post import Post
from models.comment import Comment
from models.like import Like
from models.follower import Follower
from models.thread import InnovationThread


def auth_user_action(model, id_arg_name):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()
            instance_id = kwargs.get(id_arg_name)

            if instance_id is None:
                return {"error": "Instance ID not provided."}, 400

            user = db.session.query(User).filter_by(id=user_id).first()
            if not user:
                return {"error": "User not found"}, 404
    
            instance = db.session.query(model).filter_by(id=instance_id).first()
            if not instance:
                return {"error": f"{model.__name__} with ID {instance_id} not found."}, 404
            
            is_admin = user.is_admin
            is_owner = str(instance.id) == str(user_id)

            if not is_admin and not is_owner:
                return {"error": "Unauthorized to perform this action."}, 403
            
            kwargs[id_arg_name] = instance_id
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def auth_comment_action(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        comment_id = kwargs.get('comment_id')

        if comment_id is None:
            return {"error": "Comment ID not provided."}, 400

        user = db.session.query(User).filter_by(id=user_id).first()
        if not user:
            return {"error": "User not found"}, 404

        try:
            comment = db.session.query(Comment).filter_by(id=comment_id).one()
        except NoResultFound:
            return {"error": f"Comment with ID {comment_id} not found."}, 404

        is_admin = user.is_admin
        is_owner = str(comment.user_id) == str(user_id)

        if not is_admin and not is_owner:
            return {"error": "Unauthorized to perform this action."}, 403

        return func(*args, **kwargs)
    
    return wrapper


def auth_like_action(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        like_id = kwargs.get('like_id')

        if like_id is None:
            return {"error": "Like ID not provided."}, 400

        user = db.session.query(User).filter_by(id=user_id).first()
        if not user:
            return {"error": "User not found"}, 404

        try:
            like = db.session.query(Like).filter_by(id=like_id).one()
        except NoResultFound:
            return {"error": f"Like with ID {like_id} not found."}, 404

        is_admin = user.is_admin
        is_owner = str(like.user_id) == str(user_id)

        if not is_admin and not is_owner:
            return {"error": "Unauthorized to perform this action."}, 403

        return func(*args, **kwargs)
    
    return wrapper



def auth_thread_action(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        thread_id = kwargs.get("thread_id")

        if thread_id is None:
            return {"error": "Thread ID not provided."}, 400

        user = db.session.query(User).filter_by(id=user_id).first()
        if not user:
            return {"error": "User not found"}, 404

        thread = db.session.query(InnovationThread).filter_by(id=thread_id).first()
        if not thread:
            return {"error": f"Thread with ID {thread_id} not found."}, 404

        is_admin = user.is_admin
        is_owner = str(thread.user_id) == str(user_id)

        if not is_admin and not is_owner:
            return {"error": "Unauthorized to perform this action."}, 403

        kwargs["thread_id"] = thread_id
        return func(*args, **kwargs)

    return wrapper

def auth_unfollow_action(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user_id = kwargs.get('user_id')

        if user_id is None:
            return {"error": "User ID not provided."}, 400

        if int(current_user_id) == int(user_id):
            return {"error": "You cannot follow or unfollow yourself."}, 400

        user = db.session.query(User).filter_by(id=user_id).first()
        if not user:
            return {"error": f"User with ID {user_id} not found."}, 404

        existing_follow = Follower.query.filter_by(follower_id=current_user_id, followed_id=user_id).first()
        if existing_follow is None:
            return {"error": "You are already not following this user."}, 400

        return func(*args, **kwargs)
    
    return wrapper


def get_post(post_id):
    stmt = db.select(Post).filter_by(id=post_id)
    return db.session.scalar(stmt)

def get_comment(comment_id, post_id):
    stmt = db.select(Comment).filter_by(id=comment_id, post_id=post_id)
    return db.session.scalar(stmt)

def get_user_by_id(user_id):
    stmt = db.select(User).filter_by(id=user_id)
    return db.session.scalar(stmt)

def get_thread(thread_id):
    stmt = db.select(InnovationThread).filter_by(id=thread_id)
    return db.session.scalar(stmt)

def get_thread_post(post_id, thread_id):
    stmt = db.select(Post).filter_by(id=post_id, thread_id=thread_id)
    post = db.session.scalar(stmt)

def handle_db_exceptions(error):
    db.session.rollback()
    error_map = {
        errorcodes.UNIQUE_VIOLATION: "Username or email already exists",
        errorcodes.NOT_NULL_VIOLATION: "Required field missing",
        errorcodes.FOREIGN_KEY_VIOLATION: " Invalid reference to another table",
        errorcodes.CHECK_VIOLATION: "Check constraint failed",
        errorcodes.EXCLUSION_VIOLATION: "Exclusion constraint failed"
    }
    return {"error": error_map.get(error.orig.pgcode, "Database error")}, 500