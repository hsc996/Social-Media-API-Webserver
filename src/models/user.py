from init import db, ma
from marshmallow import fields, validate
from models.follower import Follower
from marshmallow.validate import Regexp, Length


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    profile_picture_url = db.Column(db.String)
    bio = db.Column(db.String)
    date_of_birth = db.Column(db.Date)
    location = db.Column(db.String)
    website_url = db.Column(db.String)
    linkedin_url = db.Column(db.String)
    github_url = db.Column(db.String)
    job_title = db.Column(db.String)
    is_admin = db.Column(db.Boolean, default=False)

    threads = db.relationship("InnovationThread", back_populates="user")
    posts = db.relationship("Post", back_populates="user")
    comments = db.relationship("Comment", back_populates="user")
    likes = db.relationship("Like", back_populates="user")

    followers_assoc = db.relationship(
        "Follower",
        foreign_keys=[Follower.followed_id],
        back_populates="followed",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )

    following_assoc = db.relationship(
        "Follower",
        foreign_keys=[Follower.follower_id],
        back_populates="follower",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )
    


class UserSchema(ma.Schema):
    threads = fields.List(fields.Nested('InnovationThreadSchema', exclude=["user"]))
    posts = fields.List(fields.Nested('PostSchema', exclude=["user"]))
    comments = fields.List(fields.Nested('CommentSchema', exclude=["user"]))
    likes = fields.List(fields.Nested('LikeSchema', exclude=["user"]))
    followers = fields.List(fields.Nested('UserSchema', only=["id", "username"]))
    following = fields.List(fields.Nested('UserSchema', only=["id", "username"]))

    email = fields.String(
    required=True,
    validate=validate.Regexp(r"^\S+@\S+\.\S+$", error="Invalid Email Format")
    )

    password = fields.String(
        required=True,
        validate=validate.Regexp(r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$"), 
        error="Password must be a minimum of 8 characters with at least one letter and one number."
    )

    username = fields.String(
        required=True,
        validate=validate.Length(min=5, max=15, error="Username must be between 5 and 15 characters long.")
    )
    
    profile_picture_url = fields.String()
    bio = fields.String()
    date_of_birth = fields.Date()
    location = fields.String()
    website_url = fields.String()
    linkedin_url = fields.String()
    github_url = fields.String()
    skills = fields.List(fields.String())
    job_title = fields.String()

    class Meta:
        fields = ["id", "username", "email", "password", "profile_picture_url", "bio", "date_of_birth", "location", "website_url", "linkedin_url", "github_url", "skills", "job_title", "is_admin", "posts", "comment", "likes", "followed", "following", "threads"]


user_schema = UserSchema(exclude=["password"])
users_schema = UserSchema(many=True, exclude=["password"])