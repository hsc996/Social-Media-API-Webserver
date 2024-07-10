# from init import db, ma
# from marshmallow import fields

# class Post(db.Model):
#     __tablename__ = "posts"

#     id = db.Column(db.Integer, primary_key=True)
#     body = db.Column(db.String, nullable=False)
#     timestamp = db.Column(db.Date)

#     user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)


# class PostSchema(ma.Schema):
#     class Meta:
#         fields = ["id", "body", "timestamp", "user_id"]


# post_schema = PostSchema()
# posts_schema = PostSchema(many=True)