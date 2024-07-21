from datetime import date

from flask import Blueprint

from init import db, bcrypt
from models.user import User
from models.post import Post
from models.comment import Comment
from models.like import Like
from models.follower import Follower

db_commands = Blueprint("db", __name__)

@db_commands.cli.command("create")
def create_tables():
    db.create_all()
    print("Tables created")


@db_commands.cli.command("drop")
def drop_tables():
    db.drop_all()
    print("Tables dropped.")


@db_commands.cli.command("seed")
def seed_tables():
    users = [
        User(
            username="admin",
            email="admin@email.com",
            password=bcrypt.generate_password_hash("123456").decode('utf-8'),
            is_admin=True,
            profile_picture_url="http://example.com/admin.jpg",
            bio="Administrator of the platform",
            date_of_birth=date(1981, 5, 25),
            location="Palo Alto, CA",
            website_url="http://admin.com",
            linkedin_url="http://linkedin.com/admin",
            github_url="http://github.com/admin",
            skills=["Python", "Java", "C++"],
            job_title="Admin"
        ),
        User(
            username="username1",
            email="user1@email.com",
            password=bcrypt.generate_password_hash("123456").decode('utf-8'),
            profile_picture_url="http://example.com/user1.jpg",
            bio="Coding is my life!",
            date_of_birth=date(1990, 6, 15),
            location="New York, NY",
            website_url="http://user1.com",
            linkedin_url="http://linkedin.com/user1",
            github_url="http://github.com/user1",
            skills=["Javascript", "React", "Node.js"],
            job_title="Software Developer"
        ),
        User(
            username="username2",
            email="user2@email.com",
            password=bcrypt.generate_password_hash("123456").decode('utf-8'),
            profile_picture_url="http://example.com/user2.png",
            bio="Passionate about open-source.",
            date_of_birth=date(1992, 7, 25),
            location="Austin, TX",
            website_url="http://user2.com",
            linkedin_url="http://linkedin.com/in/user2",
            github_url="http://github.com/user2",
            skills=["Java", "Spring", "Docker"],
            job_title="Backend Engineer"
        ),
        User(
            username="username3",
            email="user3@email.com",
            password=bcrypt.generate_password_hash("123456").decode('utf-8'),
            profile_picture_url="http://example.com/user3.png",
            bio="AI enthusiast.",
            date_of_birth=date(1995, 8, 30),
            location="Seattle, WA",
            website_url="http://user3.com",
            linkedin_url="http://linkedin.com/in/user3",
            github_url="http://github.com/user3",
            skills=["Machine Learning", "Data Science", "Python"],
            job_title="Data Scientist"
        )
    ]

    db.session.add_all(users)

    posts = [
        Post(
            body="Body of Instagram post 1",
            timestamp=date.today(),
            user=users[1]
        ),
        Post(
            body="Body of Instagram post 2",
            timestamp=date.today(),
            user=users[0]
        ),
        Post(
            body="Body of Instagram post 3",
            timestamp=date.today(),
            user=users[1]
        )
    ]

    db.session.add_all(posts)

    comments = [
        Comment(
            comment_body="First Comment",
            timestamp=date.today(),
            user=users[1],
            posts=posts[0]
        ),
        Comment(
            comment_body="Second Comment",
            timestamp=date.today(),
            user=users[1],
            posts=posts[1]
        ),
        Comment(
            comment_body="Third Comment",
            timestamp=date.today(),
            user=users[0],
            posts=posts[2]
        ),
        Comment(
            comment_body="Fourth Comment",
            timestamp=date.today(),
            user=users[0],
            posts=posts[0]
        ),
        Comment(
            comment_body="Fifth Comment",
            timestamp=date.today(),
            user=users[2],
            posts=posts[1]
        ),
    ]
    db.session.add_all(comments)

    likes = [
        Like(
            user=users[0],
            posts=posts[0]
        ),
        Like(
            user=users[2],
            posts=posts[1]
        ),
        Like(
            user=users[0],
            posts=posts[1]
        ),
        Like(
            user=users[3],
            posts=posts[1]
        ),
        Like(
            user=users[1],
            posts=posts[2]
        )
    ]
    db.session.add_all(likes)
    db.session.commit()

    followers = [
        Follower(
            follower_id=users[1].id,
            followed_id=users[0].id
        ),
        Follower(
            follower_id=users[0].id,
            followed_id=users[1].id
        ),
        Follower(
            follower_id=users[0].id,
            followed_id=users[3].id
        ),
        Follower(
            follower_id=users[2].id,
            followed_id=users[1].id
        )
    ]
    db.session.add_all(followers)
    db.session.commit()

    print("Tables seeded.")