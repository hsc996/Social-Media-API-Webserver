from init import db, ma
from marshmallow import fields
# from models.follower import Follower

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

    # followers_assoc = db.relationship(
    #     "Follower",
    #     foreign_keys=[Follower.followed_id],
    #     back_populates="followed",
    #     lazy="dynamic",
    #     cascade="all, delete-orphan"
    # )

    # following_assoc = db.relationship(
    #     "Follower",
    #     foreign_keys=[Follower.follower_id],
    #     back_populates="followed",
    #     lazy="dynamic",
    #     cascade="all, delete-orphan"
    # )

    # def follow(self, user):
    #     if not self.is_following(user):
    #         new_follower = Follower(follower_id=self.id, followed_id=user.id)
    #         db.session.add(new_follower)

    # def unfollow(self, user):
    #     follower = self.following_assoc.filter_by(followed_id=user.id).first()
    #     if follower:
    #         db.session.delete(follower)

    # def is_following(self, user):
    #     return self.following_assoc.filter_by(followed_id=user.id).count() > 0

    # def is_followed_by(self, user):
    #     return self.followers_assoc.filter_by(follower_id=user.id).count() > 0
    


class UserSchema(ma.Schema):
    posts = fields.List(fields.Nested('PostSchema', exclude=["user"]))
    comments = fields.List(fields.Nested('CommentSchema', exclude=["user"]))
    likes = fields.List(fields.Nested('LikeSchema', exclude=["user"]))
    followers = fields.List(fields.Nested('UserSchema', only=["id", "username"]))
    following = fields.List(fields.Nested('UserSchema', only=["id", "username"]))
    
    class Meta:
        fields = ["id", "username", "email", "password", "is_admin", "posts", "comment", "likes"]


user_schema = UserSchema(exclude=["password"])
users_schema = UserSchema(many=True, exclude=["password"])