from datetime import timedelta

from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from marshmallow.exceptions import ValidationError
from psycopg2 import errorcodes
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from init import bcrypt, db
from models.user import User, user_schema, UserSchema
from utils import auth_user_action


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# View User Profile - GET - /auth/user/<int:user_id>
@auth_bp.route("/user/<int:user_id>", methods=["GET"])
def view_profile(user_id):
    """
    Retrieves a specific user's profile.

    Queries the database for a User record with the specified ID.

    Args:
        user_id (int): The ID of the user to retrieve.

    Returns:
        JSON: Serialised user profile with a 200 Ok status if the user exists.
        JSON: Error message with a 404 Not Found status if the user is not found.
    """
    stmt = db.select(User).filter_by(id=user_id)
    profile = db.session.scalar(stmt)

    if profile:
        return user_schema.dump(profile), 200
    else:
        return {"error": f"User with ID {user_id} not found."}, 404



# Register new user - POST - /auth/register
@auth_bp.route("register", methods=["POST"])
def register_user():
    """
    Registers a new user.

    Loads and validates JSON data from the request payload, creates a new user, hashes the password, and adds the user to the database.

    Returns:
        JSON: Serialised user profile with a 201 Created status upon successful registration
        JSON: Error message with a 400 Bad Request status if validation fails.
        JSON: Error message with a 409 Conflict status if a database integrity error occurs.
    """
    try:
        body_data = UserSchema().load(request.get_json())

        user = User(
            username=body_data.get("username"),
            email=body_data.get("email"),
            profile_picture_url =body_data.get("profile_pricture_url"),
            bio =body_data.get("bio"),
            date_of_birth = body_data.get("date_of_birth"),
            location =body_data.get("location"),
            website_url =body_data.get("website_url"),
            linkedin_url =body_data.get("linkedin_url"),
            github_url =body_data.get("github_url"),
            job_title =body_data.get("job_title")
        )
        password = body_data.get("password")

        if password:
            user.password = bcrypt.generate_password_hash(password).decode('utf-8')
        else:
            return {"error": "Password is required."}, 400

        db.session.add(user)
        db.session.commit()

        return user_schema.dump(user), 201
    
    except ValidationError as err:
        # Handle validation errors from UserSchema
        return {"error": err.messages}, 400
    
    except IntegrityError as err:
        db.session.rollback()
        # Handle specific PostgreSQL error codes
        if err.orig.pgcode == errorcodes.UNIQUE_VIOLATION:
            return {"error": "Username or email already exists"}, 409
        elif err.orig.pgcode == errorcodes.NOT_NULL_VIOLATION:
            return {"error": "Required field missing"}, 409
        elif err.orig.pgcode == errorcodes.UNIQUE_VIOLATION:
            return {"error": "Email address already in use"}, 409
        elif err.orig.pgcode == errorcodes.FOREIGN_KEY_VIOLATION:
            return {"error": "Invalid reference to another table"}, 409
        elif err.orig.pgcode == errorcodes.CHECK_VIOLATION:
            return {"error": "Check constraint failed"}, 409
        elif err.orig.pgcode == errorcodes.EXCLUSION_VIOLATION:
            return {"error": "Exclusion constraint failed"}, 409
        else:
            return {"error": "Database error"}, 500



# Login user - POST - /auth/login
@auth_bp.route("/login", methods=["POST"])
def login_user():
    """
    Logs in a user and creates a JWT token.

    Validates the user's email and password, then creates a JWT token for authenticated users.

    Returns:
        JSON: User's email, admin status and JWT token with a 200 OK status upon successful login.
        JSON: Error message with a 401 Unauthorized status if email or password is incorrect.
        JSON: Error message with a 500 Internal Server Error status if a database error occurs.
    """
    try:
        body_data = request.get_json()
        stmt = db.select(User).filter_by(email=body_data.get("email"))
        user = db.session.scalar(stmt)

        if user and bcrypt.check_password_hash(user.password, body_data.get("password")):
            token = create_access_token(identity=str(user.id), expires_delta=timedelta(days=1))
            return {"email": user.email, "is_admin": user.is_admin, "token": token}, 200
        else:
            return {"error": "Invalid email or password"}, 401
        
    except SQLAlchemyError:
        return {"error": "Database error"}, 500
    


# Update user - PUT, PATCH - auth/editprofile/<int:user_id>
@auth_bp.route("/editprofile/<int:user_id>", methods=["PUT", "PATCH"])
@jwt_required()
@auth_user_action(User, "user_id")
def edit_profile(user_id):
    """
    Updates users profile information.

    Loads and partially validates JSON data from the request payload to update the user's profile. Email cannot be updated.

    Args:
        user_id (int): The ID of the user to update.
    
    Returns:
        JSON: Updated user profile with a 200 OK status if successful.
        JSON: Error message with a 400 Bad Request staus if email is attempted to be updated.
        JSON: Error message with a 404 Not Found status if the user does not exist or access is unauthorised.
        JSON: Error message with a 500 Internal Server Error status if a database error occurs.
    """
    try:
        body_data = UserSchema().load(request.get_json(), partial=True)
        password = body_data.get("password")

        if "email" in body_data:
            return {"error": "This email is unique to this account and cannot be changed. Please register a new account."}, 400

        stmt = db.select(User).filter_by(id=user_id)
        user = db.session.scalar(stmt)

        if user:
            user.username = body_data.get("username") or user.username
            user.profile_picture_url = body_data.get("profile_picture_url") or user.profile_picture_url
            user.bio = body_data.get("bio") or user.bio
            user.date_of_birth = body_data.get("date_of_birth") or user.date_of_birth
            user.location = body_data.get("location") or user.location
            user.website_url = body_data.get("website_url") or user.website_url
            user.linkedin_url = body_data.get("linkedin_url") or user.linkedin_url
            user.github_url = body_data.get("github_url") or user.github_url
            user.job_title = body_data.get("job_title") or user.job_title
            if password:
                user.password = bcrypt.generate_password_hash(password).decode('utf-8')
            db.session.commit()
            return user_schema.dump(user), 200
        else:
            return {"error": "User does not exist or unauthorized access."}, 404
        
    except ValidationError as err:
        return {"error": err.messages}, 400

    except SQLAlchemyError as err:
        db.session.rollback()
        return {"error": "Database error"}, 500
    



# Delete account - DELETE - /auth/deleteaccount/<int:user_id>
@auth_bp.route("/deleteaccount/<int:user_id>", methods=["DELETE"])
@jwt_required()
@auth_user_action(User, "user_id")
def delete_account(user_id):
    """
    Deletes a user account.

    Deletes the user account with the specified ID from the database.

    Args:
        user_id (int): The ID of the user to delete.

    Returns:
        JSON: Success message with a 200 OK status if the account is deleted.
        JSON: Error message with a 404 Not Found status if the user does not exist.
        JSON: Error message with a 500 Internal Server Error status if a database error occurs.
    """
    try:
        account = User.query.get(user_id)

        if account:
            db.session.delete(account)
            db.session.commit()
            return {"message": "Account successfully deleted."}, 200
        else:
            return {"error": "User does not exist."}, 404
        
    except SQLAlchemyError as err:
        db.session.rollback()
        return {"error": "Database error."}, 500