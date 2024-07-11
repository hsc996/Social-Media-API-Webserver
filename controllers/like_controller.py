from datetime import date

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from init import db, ma
from models.like import Like, like_schema, likes_schema
from controllers.post_controller import posts_bp

likes_bp = Blueprint("likes", __name__, url_prefix="/likes")
likes_bp.register_blueprint(posts_bp)

