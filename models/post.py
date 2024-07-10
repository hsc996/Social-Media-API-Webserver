from init import db, ma
from marshmallow import fields

class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String, nullable=False)
    timestamp = db.Column(db.Date)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    user = db.relationship("User", back_populates="posts")
    comments = db.relationship("Comment", back_populates="posts", cascade="all, delete")



class PostSchema(ma.Schema):
    user = fields.Nested('UserSchema', only=["id", "username", "email"])
    comments = fields.List(fields.Nested("CommentSchema", exclude=["posts"]))

    class Meta:
        fields = ["id", "body", "timestamp", "user", "comments"]


post_schema = PostSchema()
posts_schema = PostSchema(many=True)