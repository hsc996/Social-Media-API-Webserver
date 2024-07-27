from datetime import datetime

from init import db, ma
from marshmallow import fields, validate
from sqlalchemy import func
from sqlalchemy.orm import validates

class InnovationThread(db.Model):
    __tablename__ = "threads"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    content = db.Column(db.String, nullable=False)
    timestamp = db.Column(db.DateTime, default=func.now())

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    user = db.relationship("User", back_populates="threads")
    posts = db.relationship("Post", back_populates="threads", lazy=True, cascade="all, delete-orphan")

    @validates('title')
    def validate_title(self, key, title):
        if not title:
            raise ValueError("Title must not be empty.")
        if len(title) > 100:
            raise ValueError("Title must be at most 100 characters long.")
        return title

    @validates('content')
    def validate_content(self, key, content):
        if len(content) > 5000:
            raise ValueError("Content must be at most 5000 characters long.")
        return content


class InnovationThreadSchema(ma.Schema):

    user = fields.Nested("UserSchema", only=["id", "username"])
    posts = fields.Nested("PostSchema", only=["body", "timestamp", "comments", "likes"], many=True)
    title = fields.String(
        required=True,
        validate=[
            validate.Length(min=1, error="Title must not be empty."),
            validate.Length(max=50, error="Title cannot exceed 50 characters.")
        ]
    )
    content = fields.String(
        validate=validate.Length(max=5000, error="Content cannot exceed 5000 characters.")
    )
    timestamp = fields.DateTime(format="%Y-%m-%d %H:%M:%S", missing=datetime.now)

    class Meta:
        fields = ["id", "title", "content", "timestamp", "user", "posts"]



thread_schema = InnovationThreadSchema()
threads_schema = InnovationThreadSchema(many=True)