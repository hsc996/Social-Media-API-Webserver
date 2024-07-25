from datetime import datetime

from init import db, ma
from sqlalchemy import func
from marshmallow import fields
from marshmallow.validate import Length

class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String, nullable=False)
    timestamp = db.Column(db.DateTime, default=func.now())

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    thread_id = db.Column(db.Integer, db.ForeignKey("threads.id"))

    threads = db.relationship("InnovationThread", back_populates="posts")
    user = db.relationship("User", back_populates="posts")
    comments = db.relationship("Comment", back_populates="posts", cascade="all, delete-orphan")
    likes = db.relationship("Like", back_populates="posts", cascade="all, delete-orphan")



class PostSchema(ma.SQLAlchemyAutoSchema):

    user = fields.Nested("UserSchema", only=["id", "username"])
    comments = fields.List(fields.Nested("CommentSchema", only=["id", "comment_body", "user"]))
    likes = fields.List(fields.Nested("LikeSchema"), exclude=["post_id"])
    thread = fields.Nested('InnovationThreadSchema', only=["id", "title"])

    body = fields.String(required=True,
                         validate=Length(min=1, error="Body cannot be empty.")
                         )
    
    timestamp = fields.DateTime(format="%Y-%m-%d %H:%M:%S", missing=datetime.now)


    class Meta:

        fields = ["id", "body", "timestamp", "user", "comments", "likes", "thread"]


post_schema = PostSchema()
posts_schema = PostSchema(many=True)