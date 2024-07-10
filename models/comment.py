from init import db, ma
from marshmallow import fields

class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    comment_body = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.Date)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)

    user = db.relationship("User", back_populates="comments")
    posts = db.relationship("Post", back_populates="comments")

class CommentSchema(ma.Schema):
    user = fields.Nested("UserSchema", only=["username", "email"])
    posts = fields.Nested("PostSchema", only=["body", "timestamp"])

    class Meta:
        fields = ["id", "comment_body", "timestamp", "user", "posts"]

comment_schema = CommentSchema()
comments_schema = CommentSchema(many=True)