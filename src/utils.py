from functools import wraps
from flask_jwt_extended import get_jwt_identity
from init import db
from models.user import User
from models.thread import InnovationThread
from flask import jsonify


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
