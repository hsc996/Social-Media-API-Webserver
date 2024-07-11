from init import db, ma
from marshmallow import fields

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    posts = db.relationship("Post", back_populates="user")
    comments = db.relationship("Comment", back_populates="user")
    likes = db.relationship("Like", back_populates="user")


class UserSchema(ma.Schema):
    posts = fields.List(fields.Nested('PostSchema', exclude=["user"]))
    comments = fields.List(fields.Nested('CommentSchema', exclude=["user"]))
    likes = fields.List(fields.Nested('LikeSchema', exclude=["user"]))
    
    class Meta:
        fields = ["id", "username", "email", "password", "is_admin", "posts", "comment", "likes"]


user_schema = UserSchema(exclude=["password"])
users_schema = UserSchema(many=True, exclude=["password"])