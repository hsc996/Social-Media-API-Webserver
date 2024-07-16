from init import db, ma
from marshmallow import fields

class Follower(db.Model):

    __tablename__ = "followers"

    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)

    follower = db.relationship("User", foreign_keys=[follower_id], back_populates="following_assoc")
    followed = db.relationship("User", foreign_keys=[followed_id], back_populates="followers_assoc")



class FollowerSchema(ma.Schema):
    class Meta:
        fields = ["follower_id", "followed_id"]


follower_schema = FollowerSchema()
followers_schema = FollowerSchema(many=True)