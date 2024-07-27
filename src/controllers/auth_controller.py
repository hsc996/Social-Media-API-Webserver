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
    # SQLAlchemy statement (query) to select a User, based on the user_id provided
    stmt = db.select(User).filter_by(id=user_id)
    # Execution of the statement to retrieve a single result (as scalar is singular) from the database
    profile = db.session.scalar(stmt)

    # If the user profile exists
    if profile:
        # Serialise the data using the schema/return it with a 200 OK status
        return user_schema.dump(profile), 200
    # If the profile (user_id) requested does not exist
    else:
        # Return error message with a 404 Not Found status
        return {"error": f"User with ID {user_id} not found."}, 404



# Register new user - POST - /auth/register
@auth_bp.route("register", methods=["POST"])
def register_user():
    try:
        # Load and validate JSON data from the payload using UserSchema
        body_data = UserSchema().load(request.get_json())

        # Create a new user instance using the validated data
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
        # Retrieve the password from the request data
        password = body_data.get("password")

        # If the password is provided
        if password:
            # Hash the password and apply it to the user object
            user.password = bcrypt.generate_password_hash(password).decode('utf-8')
        # If the password is not provided
        else:
            # Return error 400 Bad Request error if no password is provided
            return {"error": "Password is required."}, 400

        # Add the new user to the database session
        db.session.add(user)
        # Commit the session to save the user to the database
        db.session.commit()

        # Return the newly created user data with a 201 Created status
        return user_schema.dump(user), 201
    
    except ValidationError as err:
        # Handle validation errors from UserSchema
        return {"error": err.messages}, 400
    
    except IntegrityError as err:
        # Roll back the session in case of database integrity errors
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



# Login user - POST - auth/login
@auth_bp.route("/login", methods=["POST"])
def login_user():
    try:
        # Get JSON data from the request
        body_data = request.get_json()

        # SQLAlchemy statement (query) to select a User, based on the email provided
        stmt = db.select(User).filter_by(email=body_data.get("email"))
        # Execution of the statement to retrieve a single result (as scalar is singular) from the database
        user = db.session.scalar(stmt)

        # Conditional statement to check if user exists and password is correct
        if user and bcrypt.check_password_hash(user.password, body_data.get("password")):
            # Create a JWT token for the user, which will expire after 24 hours
            token = create_access_token(identity=str(user.id), expires_delta=timedelta(days=1))
            # Return the user's email, admin status, and token with a 200 OK status
            return {"email": user.email, "is_admin": user.is_admin, "token": token}, 200
        else:
            # Return an error if email or password is incorrect
            return {"error": "Invalid email or password"}, 401
        
    except SQLAlchemyError:
        # Return an error if database error occurs
        return {"error": "Database error"}, 500
    


# Update user - PUT, PATCH - auth/editprofile/<int:user_id>
@auth_bp.route("/editprofile/<int:user_id>", methods=["PUT", "PATCH"])
@jwt_required()
@auth_user_action(User, "user_id")
def edit_profile(user_id):
    try:
        # Load and partially validate the JSON data from the payload using UserSchema -- this will enable the user to update only specific fields without requiring all fields to be present within the payload request.
        body_data = UserSchema().load(request.get_json(), partial=True)
        # Retrieve the password from the request data if provided
        password = body_data.get("password")

        # Prevents email from being updated by returning an error if email is in the data. This because the email is linked to the account, thus prompting the user to create another account if they would like to use a different email address.
        if "email" in body_data:
            return {"error": "This email is unique to this account and cannot be changed. Please register a new account."}, 400

        # SQLAlchemy statement (query) to select a User, based on the user_id provided
        stmt = db.select(User).filter_by(id=user_id)
        # Execution of the statement to retrieve a single result (as scalar is singular) from the database
        user = db.session.scalar(stmt)

        # Conditional statement to check whether the user exists based off the user_id provided
        if user:
            # Update user fields with new data if provided, otherwise keep existing values
            user.username = body_data.get("username") or user.username
            user.profile_picture_url = body_data.get("profile_picture_url") or user.profile_picture_url
            user.bio = body_data.get("bio") or user.bio
            user.date_of_birth = body_data.get("date_of_birth") or user.date_of_birth
            user.location = body_data.get("location") or user.location
            user.website_url = body_data.get("website_url") or user.website_url
            user.linkedin_url = body_data.get("linkedin_url") or user.linkedin_url
            user.github_url = body_data.get("github_url") or user.github_url
            user.job_title = body_data.get("job_title") or user.job_title
            # Hash and update the password if requested
            if password:
                user.password = bcrypt.generate_password_hash(password).decode('utf-8')
            # Commit the changes tp the database
            db.session.commit()
            # Return the updated user data with a 200 OK status
            return user_schema.dump(user), 200
        else:
            # Return an error if the user does nto exist/acces is unauthorised
            return {"error": "User does not exist or unauthorized access."}, 404
        
    except ValidationError as err:
        # Handle validation errors from UserSchema
        return {"error": err.messages}, 400

    except SQLAlchemyError as err:
        # Roll back the sessio in case of database errors
        db.session.rollback()
        # Return a database 500 staus error message to the user
        return {"error": "Database error"}, 500
    



# Delete account - DELETE - /auth/deleteaccount/<int:user_id>
@auth_bp.route("/deleteaccount/<int:user_id>", methods=["DELETE"])
@jwt_required()
@auth_user_action(User, "user_id")
def delete_account(user_id):
    try:
        # Simplified query to the database to find the user with the specified user_id
        account = User.query.get(user_id)

        # Check if user account exists
        if account:
            # Delete the user account from the database
            db.session.delete(account)
            # Commit the changes to confirm the deletion
            db.session.commit()
            # Return message to indicate the action was successful, with a 200 OK status
            return {"message": "Account successfully deleted."}, 200
        else:
            # Return an error if the user does nto exist
            return {"error": "User does not exist."}, 404
        
    except SQLAlchemyError as err:
        # Roll back the sessio in case of database errors
        db.session.rollback()
        # Return a database 500 staus error message to the user
        return {"error": "Database error."}, 500