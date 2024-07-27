from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow.exceptions import ValidationError

from init import db
from models.follower import Follower, follower_schema, followers_schema
from models.user import User
from utils import auth_unfollow_action


follower_bp = Blueprint("follower", __name__, url_prefix="/users")


# Fetches followers of a specific user - GET - /users/<int:user_id>/followers
@follower_bp.route("/<int:user_id>/followers", methods=["GET"])
def get_followers(user_id):
    """
    Fetches the followers of a specific user.

    Args:
        user_id (int): The ID of the user.

    Returns:
        JSON: Serialised followers with a 200 OK status if successful.
        JSON: Error message with a 404 Not Found status if the user is not found.
    """
    stmt = db.select(User).filter_by(id=user_id)
    user = db.session.scalar(stmt)

    if user is None:
        return {"error": f"User with ID {user_id} not found."}, 404
    
    followers = user.followers_assoc.all()
    return followers_schema.dump(followers), 200



# /users/<int:user_id>/following
@follower_bp.route("/<int:user_id>/following", methods=["GET"])
def get_following(user_id):
    """
    Fetches the users that a specific user is following.

    Args:
        user_id (int): The ID of the user.
    
    Returns:
        JSON: Serialised following list with a 200 OK status if successful.
        JSON: Error message with a 404 Not Found status if the user is not found.
    """
    user_stmt = db.select(User).filter_by(id=user_id)
    user = db.session.scalar(user_stmt)

    if user is None:
        return {"error": f"User with ID {user_id} not found."}, 404

    followed_stmt = db.select(Follower.followed_id).filter_by(follower_id=user_id)
    followed_ids = db.session.scalars(followed_stmt).all()

    if not followed_ids:
        return {"message": "This user is not following anyone."}, 200

    following_list = [{"follower_id": user_id, "followed_id": followed_id} for followed_id in followed_ids]

    return following_list, 200

    


# Follows a specific user - POST - /users/follow
@follower_bp.route("/follow", methods=["POST"])
@jwt_required()
def follow():
    """
    Follows a specific user.

    Users can follow other users except themselves.

    Returns:
        JSON: Serialised follow data with a 201 Created status if successful.
        JSON: Error message with a 404 Not Found status if the user to follow is not found.
        JSON: Error message with a 400 Bad Request status if invalid input or user has already been followed.
    """
    current_user_id = get_jwt_identity()
    try:
        followed_id = request.json.get("followed_id")
        if followed_id is None:
            return {"error": "Missing 'followed_id' in request."}, 400
        
        followed_id = int(followed_id)
        stmt = db.select(User).where(User.id == followed_id)
        user_to_follow = db.session.scalar(stmt)

        if user_to_follow is None:
            return {"error": f"User with ID {followed_id} not found"}, 404

        if int(current_user_id) == followed_id:
            return {"error": "You cannot follow yourself."}, 400

        existing_follow = Follower.query.filter_by(follower_id=current_user_id, followed_id=followed_id).first()
        if existing_follow:
            return {"error": "You are already following this user."}, 400
        
        new_follow = Follower(
            follower_id=current_user_id,
            followed_id=followed_id
        )
        db.session.add(new_follow)
        db.session.commit()

        return follower_schema.dump(new_follow), 201
        
    except ValidationError as e:
        return {"error": str(e)}, 400
    
    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 500




# Unfollow a specific user - DELETE - /users/<int:user_id>/unfollow
@follower_bp.route("/<int:user_id>/unfollow", methods=["DELETE"])
@jwt_required()
@auth_unfollow_action
def unfollow_user(user_id):
    """
    Unfollow a specific user.

    Args:
        user_id (int): The ID of the user to unfollow.

    Return:
        JSON: Success message with a 200 OK status if successful.
        JSON: Error message with a 404 Not Found status if user is not found.
        JSON: Error message with a 400 Bad Request status if the user is not followed.
    """
    current_user_id = get_jwt_identity()
    try:
        if int(current_user_id) == int(user_id):
            return {"error": "You cannot follow or unfollow yourself."}, 400
        
        stmt = db.select(User).filter_by(id=user_id)
        user_to_unfollow = db.session.scalar(stmt)

        if user_to_unfollow is None:
            return {"error": f"User with ID {user_id} not found."}, 404

        existing_follow = Follower.query.filter_by(follower_id=current_user_id, followed_id=user_id).first()
        if existing_follow is None:
            return {"error": "You are already not following this user."}, 400
        
        db.session.delete(existing_follow)
        db.session.commit()

        return {"message": f"You have successfully unfollowed user with ID {user_id}"}, 200

    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 500
    

