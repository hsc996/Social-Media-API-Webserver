from flask_jwt_extended import get_jwt_identity
from init import db
from models.user import User


def authorise_as_admin():
    user_id = get_jwt_identity()
    stmt = db.select(User).filter_by(id=user_id)
    user = db.session.scalar(stmt)

    return user.is_admin