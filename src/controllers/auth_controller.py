from datetime import timedelta

from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from marshmallow.exceptions import ValidationError
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from init import bcrypt, db
from models.user import User, user_schema, UserSchema
from utils import auth_user_action, handle_db_exceptions, get_user_by_id


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
    profile = get_user_by_id(user_id)
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
        password = body_data.get("password")

        if not password:
            return {"error": "Password is required."}, 400


        user = User(**body_data)
        user.password = bcrypt.generate_password_hash(password).decode('utf-8')

        db.session.add(user)
        db.session.commit()

        return user_schema.dump(user), 201
    
    except ValidationError as err:
        # Handle validation errors from UserSchema
        return {"error": err.messages}, 400
    
    except IntegrityError as err:
        return handle_db_exceptions(err)



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
        email = body_data.get("email", "").strip().lower()
        stmt = db.select(User).filter_by(email=email)
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

        user = get_user_by_id(user_id)

        if user:
            for key, value in body_data.items():
                if key != "password":
                    setattr(user, key, value.strip() if isinstance(value,str) else value)
            if password:
                user.password = bcrypt.generate_password_hash(password).decode('utf-8')
            db.session.commit()
            return user_schema.dump(user), 200
        else:
            return {"error": "User does not exist or unauthorized access."}, 404
        
    except ValidationError as err:
        return {"error": err.messages}, 400

    except SQLAlchemyError:
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
        account = get_user_by_id(user_id)

        if account:
            db.session.delete(account)
            db.session.commit()
            return {"message": "Account successfully deleted."}, 200
        else:
            return {"error": "User does not exist."}, 404
        
    except SQLAlchemyError:
        return {"error": "Database error."}, 500