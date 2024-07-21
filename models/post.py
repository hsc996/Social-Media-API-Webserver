from init import db, ma
from marshmallow import fields, validates, ValidationError

class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String, nullable=False)
    timestamp = db.Column(db.Date)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    user = db.relationship("User", back_populates="posts")
    comments = db.relationship("Comment", back_populates="posts", cascade="all, delete")
    likes = db.relationship("Like", back_populates="posts")



class PostSchema(ma.SQLAlchemyAutoSchema):
    user = fields.Nested('UserSchema', only=["id", "username", "email"])
    comments = fields.List(fields.Nested("CommentSchema", exclude=["posts"]))
    likes = fields.List(fields.Nested('LikeSchema'))

    body = fields.String(required=True)
    timestamp = fields.Date(format="%Y-%m-%d")

    @validates('body')
    def validates_body(self, value):
        if not value.strip():
            raise ValidationError("Body must be a non-empty string.")


    class Meta:
        fields = ["id", "body", "timestamp", "user", "comments", "likes"]


post_schema = PostSchema()
posts_schema = PostSchema(many=True)