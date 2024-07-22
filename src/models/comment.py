from src.init import db, ma
from marshmallow import fields, validates, ValidationError
from marshmallow.validate import Length, Range, Regexp



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
    user = fields.Nested("UserSchema", only=["username"])
    posts = fields.Nested("PostSchema", only=["body", "timestamp", "thread_id"])

    comment_body = fields.String(
        required=True,
        validate=Length(min=1, max=200, error="Comment must be between 1 and 200 characters.")
    )

    timestamp = fields.Date(
        format="%Y-%m-%d", error="Timestamp must be in YYYY-MM-DD format."
    )

    @validates("comment_body")
    def validate_comment_body(self, value):
        if not value.strip():
            raise ValidationError("Comment body cannot be empty.")

    class Meta:
        fields = ["id", "comment_body", "timestamp", "user", "posts"]

comment_schema = CommentSchema()
comments_schema = CommentSchema(many=True)