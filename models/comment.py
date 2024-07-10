# from init import db, ma
# from marshmallow import fields

# class Comment(db.Model):
#     __tablename__ = "comments"

#     id = db.Column(db.Integer, primary_key=True)
#     comment_body = db.Column(db.String(200), nullable=False)
#     timestamp = db.Column(db.Date)

#     user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
#     post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)

# class CommentSchema(ma.Schema):
#     user = fields.Nested("UserSchema", only=["name", "email"])
#     post = fields.Nested("PostSchema", only=["body", "timestamp"])

#     class Meta:
#         fields = ["id", "body", "timestamp", "user_id", "post_id"]

# comment_schema = CommentSchema()
# comments_schema = CommentSchema(many=True)