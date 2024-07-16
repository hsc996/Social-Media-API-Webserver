from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from sqlalchemy.orm.exc import NoResultFound

from init import db, ma
from models.follower import Follower, follower_schema, followers_schema
from models.user import User


follower_bp = Blueprint("follower", __name__, url_prefix="/users/<int:user_id>")


# Get followers of a user - GET - /user/user_id/followers
@follower_bp.route("/followers", methods=["GET"])
def get_followers(user_id):
    try:
        stmt = db.select(User).filter_by(id=user_id)
        user = db.session.scalar(stmt)

        if user:
            followers = Follower.query.filter_by(followed_id=user_id).all()
            return followers_schema.dump(followers), 200
        
    except NoResultFound:
        return {"error": f"User with ID {user_id} not found."}, 404


# Get users a specific user is following - GET - /user/user_id/following
@follower_bp.route("/following", methods=["GET"])
def get_following(user_id):
    try:
        stmt = db.select(User).filter_by(id=user_id)
        user = db.session.scalar(stmt)

        if user:
            following = Follower.query.filter_by(follower_id=user_id).all()
            return followers_schema.dump(following), 200
        
    except NoResultFound:
        return {"error": f"User with ID {user_id} not found."}, 404
    


# Follower a user - POST - /user/user_id/followers
@follower_bp.route("/followers", methods=["POST"])
@jwt_required()
def follow(user_id):
    current_user_id = get_jwt_identity()

    try:
        schema = follower_schema
        validated_data = schema.load(request.json)
        followed_id = validated_data["user_id"]

        if current_user_id == followed_id:
            return {"error": "You can not follow or unfollow yourself"}, 400

        stmt = db.select(User).filter_by(id=followed_id)
        user_to_follow = db.session.scalar(stmt)

        if not user_to_follow:
            return {"error": f"User with ID {user_id} not found"}, 404

        existing_follow = Follower.query.filter_by(follower_id=current_user_id, followed_id=user_id).first()
        if existing_follow:
            return {"error": "You are already following this user."}
        
        new_follow = Follower(
            follower_id=current_user_id,
            followed_id=user_id
        )
        db.session.add(new_follow)
        db.session.commit()

        return follower_schema.dump(new_follow), 201
        
    except ValidationError as e:
        return {"error": str(e)}, 400
        
    except NoResultFound:
        return {"error": f"User with ID {user_id} not found"}, 404
    

# Unfollow a user - DELETE - /user/user_id/followers
@follower_bp.route("/followers", methods=["DELETE"])
@jwt_required()
def unfollow_user(user_id):
    current_user_id = get_jwt_identity()

    if current_user_id == user_id:
        return {"error": "You can not follow or unfollow yourself"}, 400
    
    try:
        stmt = db.select(User).filter_by(id=user_id)
        user_to_unfollow = db.session.scalar(stmt)

        if user_to_unfollow:
            existing_follow = Follower.query.filter_by(follower_id=current_user_id, followed_id=user_id).first()
            if not existing_follow:
                return {"error": "You are already not following this user."}, 404
            
            db.session.delete(existing_follow)
            db.session.commit()

            return {"message": f"You have successfully unfollowed user with ID {user_id}"}
        
    except NoResultFound:
        return {"error": f"User with ID {user_id} not found."}, 404
    
    except Exception as e:
        return {"error": str(e)}, 500
    

