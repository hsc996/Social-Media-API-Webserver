from src.init import db, ma
from marshmallow import fields, validates, ValidationError
from marshmallow.validate import Range, OneOf

class Follower(db.Model):

    __tablename__ = "followers"

    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)

    follower = db.relationship("User", foreign_keys=[follower_id], back_populates="following_assoc")
    followed = db.relationship("User", foreign_keys=[followed_id], back_populates="followers_assoc")

    __table_args__ = (
        db.UniqueConstraint('follower_id', 'followed_id', name='unique_follow_pair'),
    )

class FollowerSchema(ma.Schema):

    follower_id = fields.Integer(
        required=True,
        validate=Range(min=1, error="Follower ID must be a positive integer.")
    )

    followed_id = fields.Integer(
        required=True,
        validate=Range(min=1, error="Followed ID must be a positive integer.")
    )

    @validates("follower_id")
    def validate_follower_id(self, value):
        if value <= 0:
            raise ValidationError("Follower ID must be a positive integer.")
    
    @validates("followed_id")
    def validate_followed_id(self, value):
        if value <= 0:
            raise ValidationError("Follower ID must be a positive integer.")

    class Meta:
        fields = ["follower_id", "followed_id"]


follower_schema = FollowerSchema()
followers_schema = FollowerSchema(many=True)