# from flask import Blueprint, request
# from flask_jwt_extended import jwt_required, get_jwt_identity

# from init import db, ma
# from models.follower import Follower, follower_schema, followers_schema
# from models.user import User, user_schema

# follower_bp = Blueprint("follower", __name__, url_prefix="/<int:user_id>")

# @follower_bp.route("/", methods=["POST"])
# def follow(user_id):
#     pass