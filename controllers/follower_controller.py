from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from init import db, ma
from models.follower import Follower, follower_schema, followers_schema
from models.user import User


follower_bp = Blueprint("follower", __name__, url_prefix="/users/<int:user_id>")


# Get followers of a user - GET - /users/<user_id>/followers
@follower_bp.route("/followers", methods=["GET"])
def get_followers(user_id):
    stmt = db.select(User).filter_by(id=user_id)
    user = db.session.scalar(stmt)

    if user is None:
        return {"error": f"User with ID {user_id} not found."}, 404
    
    followers = Follower.query.filter_by(followed_id=user_id).all()
    return followers_schema.dump(followers), 200




# Get users a specific user is following - GET - /users/<user_id>/following
@follower_bp.route("/following", methods=["GET"])
def get_following(user_id):
    stmt = db.select(User).filter_by(id=user_id)
    user = db.session.scalar(stmt)

    if user is None:
        return {"error": f"User with ID {user_id} not found."}, 404
    
    following = Follower.query.filter_by(follower_id=user_id).all()
    return followers_schema.dump(following), 200

    


# Follow a user - POST - /users/<user_id>/followers
@follower_bp.route("/followers", methods=["POST"])
@jwt_required()
def follow(user_id):
    current_user_id = get_jwt_identity()

    try:
        schema = follower_schema
        validated_data = schema.load(request.json)
        followed_id = validated_data["user_id"]

        if current_user_id == followed_id:
            return {"error": "You cannot follow or unfollow yourself"}, 400

        stmt = db.select(User).filter_by(id=followed_id)
        user_to_follow = db.session.scalar(stmt)

        if user_to_follow is None:
            return {"error": f"User with ID {user_id} not found"}, 404

        existing_follow = Follower.query.filter_by(follower_id=current_user_id, followed_id=user_id).first()
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

    

# Unfollow a user - DELETE - /users/<user_id>/followers
@follower_bp.route("/followers", methods=["DELETE"])
@jwt_required()
def unfollow_user(user_id):
    current_user_id = get_jwt_identity()

    if current_user_id == user_id:
        return {"error": "You cannot follow or unfollow yourself."}, 400
    
    try:
        stmt = db.select(User).filter_by(id=user_id)
        user_to_unfollow = db.session.scalar(stmt)

        if user_to_unfollow is None:
            return {"error": f"User with ID {user_id} not found."}, 404
        
        existing_follow = Follower.query.filter_by(follower_id=current_user_id, followed_id=user_id).first()
        if existing_follow is None:
            return {"error": "You are already not following this user."}, 404
        
        db.session.delete(existing_follow)
        db.session.commit()

        return {"message": f"You have successfully unfollowed user with ID {user_id}"}, 200

    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}, 500
    

