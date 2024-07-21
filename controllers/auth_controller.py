from datetime import timedelta

from flask import Blueprint, request
from sqlalchemy.exc import IntegrityError
from psycopg2 import errorcodes
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from init import bcrypt, db
from models.user import User, user_schema, UserSchema


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# Register new user - POST - /auth/register
@auth_bp.route("register", methods=["POST"])
def register_user():
    try:
        body_data = request.get_json()
        body_data = UserSchema().load(request.get_json())

        user = User(
            username=body_data.get("username"),
            email=body_data.get("email")
        )
        password = body_data.get("password")

        if password:
            user.password = bcrypt.generate_password_hash(password).decode('utf-8')

        db.session.add(user)
        db.session.commit()

        return user_schema.dump(user), 201
    
    except IntegrityError as err:
        # not null violation
        if err.orig.pgcode == errorcodes.NOT_NULL_VIOLATION:
            return {"error": f"The column {err.orig.diag.column_nameq} required"}, 409
            # unique violation
        elif err.orig.pgcode == errorcodes.UNIQUE_VIOLATION:
            return {"error": "Email address already in use"}, 409
        else:
            return {"error": "Database error"}, 500



# Login user - POST - auth/login
@auth_bp.route("/login", methods=["POST"])
def login_user():
    body_data = request.get_json()

    stmt = db.select(User).filter_by(email=body_data.get("email"))
    user = db.session.scalar(stmt)

    if user and bcrypt.check_password_hash(user.password, body_data.get("password")):
        token = create_access_token(identity=str(user.id), expires_delta=timedelta(days=1))
        return {"email": user.email, "is_admin": user.is_admin, "token": token}, 200
    else:
        return {"error": "Invalid email or password"}, 401
    

# Update user - PUT, PATCH - auth/users/user_id
@auth_bp.route("/users", methods=["PUT", "PATCH"])
@jwt_required()
def update_user():
    body_data = UserSchema().load(request.get_json(), partial=True)
    password = body_data.get("password")

    stmt = db.select(User).filter_by(id=get_jwt_identity())
    user = db.session.scalar(stmt)

    if user:
        user.name = body_data.get("name") or user.name
        if password:
            user.password = bcrypt.generate_password_hash(password).decode('utf-8')
        db.session.commit()
        return user_schema.dump(user)
    else:
        return {"error": "User does not exist."}