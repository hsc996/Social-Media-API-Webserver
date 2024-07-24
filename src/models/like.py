from init import db, ma
from marshmallow import fields


class Like(db.Model):
    __tablename__ = "likes"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)

    user = db.relationship("User", back_populates="likes")
    posts = db.relationship("Post", back_populates="likes")


class LikeSchema(ma.Schema):
    user = fields.Nested("UserSchema", only=["username"])
    posts = fields.Nested("PostSchema", only=["id"])

    class Meta:
        fields = ["id", "user_id", "post_id"]

like_schema = LikeSchema()
likes_schema = LikeSchema(many=True)