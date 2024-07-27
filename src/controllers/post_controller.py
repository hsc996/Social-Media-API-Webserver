from datetime import datetime, date

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow.exceptions import ValidationError

from init import db
from models.post import Post, post_schema, posts_schema
from models.like import Like
from models.comment import Comment
from models.thread import InnovationThread
from controllers.comment_controller import comments_bp
from utils import auth_user_action


posts_bp = Blueprint("posts", __name__, url_prefix="/posts")
posts_bp.register_blueprint(comments_bp)


# POST CONTROLLERS ALLOWING USERS TO POST FROM THEIR ACCOUNT


# Fetch all posts - GET - /posts
@posts_bp.route("/", methods=["GET"])
def get_all_posts():
    """
    Retrieves all posts from the datase, ordered by timestamp in descending order.

    Queries the database for all Post records, orders them by timestamp in descending order, and returns the serialised list of posts.

    Returns:
    JSON: Serialised list of all posts with a 200 OK status if posts exist.
    JSON: Error message with a 404 Not Found status if no posts are found.
    """
    # Query to select all posts ordered by timestamp (desc).
    stmt = db.select(Post).order_by(Post.timestamp.desc())
    # Retrieve all posts.
    posts = db.session.scalars(stmt)

    if posts:
         # Serialise the data and return posts if any exist.
         return posts_schema.dump(posts), 200
    else:
        # Return error message if no posts are found.
        return {"error": "No posts found."}, 404


# Fetch a single post - GET - /posts/<int:post_id>
@posts_bp.route("/<int:post_id>", methods=["GET"])
def get_single_post(post_id):
    """
    Retrieves a single post via its ID.

    Queries the database for a Post record with the specified ID and returns the serialised post.

    Args:
        post_id (int): The ID of the post to retrieve.

    Return:
        JSON: Serialised post with a 200 OK status if the post exists.
        JSON: Error message with a 404 Not Found status if the post is not found.
    """
    # Query to select a post by its ID.
    stmt = db.select(Post).filter_by(id=post_id)
    # Execute the query to retrieve a single post.
    post = db.session.scalar(stmt)
    if post:
        # Serialise the data and return the post.
        return post_schema.dump(post), 200
    else:
        # Return an error message if the post is not found.
        return {"error": f"Post with ID {post_id} not found."}, 404


# Create a post - POST - /posts
@posts_bp.route("/", methods=["POST"])
@jwt_required()
def create_post():
    """
    Creates a new post.

    Validates the request body data, creates a new Post record with the provided data, and stores it in the database.

    Returns:
        JSON: Serialised new post with a 201 Created status if creation is successful.
        JSON: Error message with a 400 Bad Reuqest status if the request body is invalid.
        JSON: Error message with a 500 Internal Server Error status if an exception occur.
    """
    try:
        # Load and validate the request data.
        body_data = post_schema.load(request.get_json())

        if not body_data or not isinstance(body_data["body"], str) or not body_data.get("body").strip():
            return {"error": "Invalid request body"}, 400
        
        # Create a new Post object.
        new_post = Post(
            body=body_data.get("body"),
            timestamp=date.today(),
            user_id=get_jwt_identity()
        )
        # Add the new post to the session and commit it to the database.
        db.session.add(new_post)
        db.session.commit()

        # Serialises the data and returns the new post.
        return post_schema.dump(new_post), 201
    
    except ValidationError as e:
        return {"error": str(e)}, 400
    
    except Exception as e:
        db.session.rollback()
        return {"error": "Internal Server Error"}, 500



# Edit a post - PUT, PATCH - /posts/<int:post_id>
@posts_bp.route("/<int:post_id>", methods=["PUT", "PATCH"])
@jwt_required()
@auth_user_action(Post, "post_id")
def update_post(post_id):
    """
    Updates an existing post by its ID.

    Validates the request body data, updates the Post record witht the specified ID, and commits the changes to the database.

    Args:
        post_id (int): The ID of the post to update.

    Return:
        JSON: Serlialised updated post with a 200 OK status if update is successful.
        JSON: Error message with a 404 Not Found status if the post is not found.
        JSON: Error message with a 400 Bad Request status if the request body is invalid.
        JSON: Error message with a 500 Internal Sevrer Error status if an excpetion occurs.
    """
    try:
        # Load and validate the request data, allowing partial updates.
        body_data = post_schema.load(request.get_json(), partial=True)
        # Query to select the post by ID.
        stmt = db.select(Post).filter_by(id=post_id)
        post = db.session.scalar(stmt)

        if not post:
            return {"error": f"Post with ID {post_id} not found."}, 404
        
        if not body_data or not isinstance(body_data["body"], str) or not body_data.get("body").strip():
            return {"error": "Invalid request body"}, 400

        # Update post fields with the new values from the request data.
        post.body = body_data.get("body", post.body)
        if body_data.get("timestamp"):
            post.timestamp = datetime.strptime(body_data["timestamp"], "%Y-%m-%d").date()

        # Commit the changes to the database.
        db.session.commit()
        
        # Serialises the data and return the updated post.
        return post_schema.dump(post), 200
    
    except ValidationError as e:
        return {"error": e.messages}, 400
    
    except Exception as e:
        db.session.rollback()
        return {"error": "Internal Server Error"}, 500
    



# Delete a post - DELETE - /posts/<int:post_id>
@posts_bp.route("/<int:post_id>", methods=["DELETE"])
@jwt_required()
@auth_user_action(Post, "post_id")
def delete_post(post_id):
    """
    Deletes a post by its ID.

    Removes the Post record with the speicfied ID from the database, along with all associated lieks and comments.

    Args:
        post_id (int): The ID of the post to delete.

    Returns:
        JSON: Success message with a 200 OK status fi deletion is successful.
        JSON: Error message with a 404 Not Found status if the post is not found.
        JSON: Error message with a 500 Internal Server Error status if an exception occurs.
    """
    try:
        # Query to fetch the post by its ID.
        post = Post.query.get(post_id)
        
        if not post:
            return {"error": f"Post with ID {post_id} not found."}, 404
        
        # Delete associated likes and comments.
        db.session.query(Like).filter_by(post_id=post_id).delete()
        db.session.query(Comment).filter_by(post_id=post_id).delete()

        # Delete the post and commit the changes.
        db.session.delete(post)
        db.session.commit()

        return {"message": f"Post with ID {post_id} successfully deleted."}, 200
    
    except Exception as e:
        db.session.rollback()
        print(e)
        return {"error": "Internal Server Error"}, 500
    



# POST CONTROLLERS THAT ALLOW USERS TO POST WITHIN EXISTING INNOVATION THREADS



# Get all posts on a specific thread - GET - /posts/threads/<int:thread_id>
@posts_bp.route("threads/<int:thread_id>", methods=["GET"])
def get_all_posts_in_thread(thread_id):
    """
    Retrieves all posts in a specific thread.

    Queries the database for all Post records within a specific thread, ordered by timestamp in descending order.

    Args:
        thread_id (int): The ID of the thread to retrieve posts from.

    Returns:
        JSON: Serialised list of posts within the thread with a 200 OK status if posts exist.
        JSON: Error message with a 404 Not Found status ifi no posts are found in the thread. 
    """
    try:
        # Query to select posts by thead ID, ordered by timestamp (desc).
        stmt = db.select(Post).filter_by(thread_id=thread_id).order_by(Post.timestamp.desc())
        posts = db.session.scalars(stmt).all()

        if not posts:
            return {"error": f"No posts found in Thread with ID {thread_id}."}, 404
        
        return posts_schema.dump(posts), 200
    
    except Exception as e:
        print(f"Error: {e}")
        return {"error": "Internal Server Error."}, 500
    


# Get a specfic post on a specific thread - GET - /posts/<int:post_id>/threads/<int:thread_id>
@posts_bp.route("<int:post_id>/threads/<int:thread_id>", methods=["GET"])
def get_posts_in_thread(thread_id, post_id):
    """
    Retrieves a specific post in a speicific thread.

    Queries the database for a Post record with the specified ID within a given thread.

    Args:
        thread_id (int): The ID of the thread to reitreve the post from.
        post_id (int): The ID of the post to retrieve.

    Returns:
        JSON: Serialised post with a 200 OK status if the post exists within the thread.
        JSON: Error message with a 404 Not Found status fi the post is not found within the thread.
    """
    try:
        # Query to select a post by thread ID and post ID.
        stmt = db.select(Post).filter_by(id=post_id, thread_id=thread_id)
        post = db.session.scalar(stmt)

        if not post:
            return {"error": f"Post with ID {post_id} not found in Thread with ID {thread_id}."}, 404
        
        return post_schema.dump(post), 200
    
    except Exception as e:
        return {"error": "Internal Server Error."}, 500
    


# Post to a specific thread - POST - /posts/threads/<int:thread_id>
@posts_bp.route("/threads/<int:thread_id>", methods=["POST"])
@jwt_required()
def post_to_thread(thread_id):
        """
        Creates a new posts in a specific thread.

        Validates the request body data, creates a new Post record within the specified thread, and stores it in the database.

        Args:
            thread_id (int): The ID of the thread to post to.

        Returns:
            JSON: Serialised new post with a 201 Created status if creation is successful.
            JSON: Error message with a 400 Bad Request status if the request body is invalid.
            JSON: Error messge with a 404 Not Found status if the specified thread does not exist.
            JSON: Error message with a 500 Internal Server Error status if an exception occurs.
        """
        try:
            # Load and validate the request data.
            body_data = post_schema.load(request.get_json())

            if not body_data or not isinstance(body_data["body"], str) or not body_data.get("body").strip():
                return {"error": "Invalid request body"}, 400
            
            # Check if the specified thread exists.
            stmt = db.select(InnovationThread).filter_by(id=thread_id)
            thread = db.session.scalar(stmt)

            if thread is None:
                return {"error": f"Thread with ID {thread_id} not found."}, 404
            
            # Create a new Post object in the specified thread.
            new_post = Post(
                body=body_data.get("body"),
                timestamp=date.today(),
                user_id=get_jwt_identity(),
                thread_id=thread_id
            )
            # Add the new post to the session and commit it to the database.
            db.session.add(new_post)
            db.session.commit()

            return post_schema.dump(new_post), 201
        
        except ValidationError as e:
            return {"error": str(e)}, 400
    
        except Exception as e:
            db.session.rollback()
            print(e)
            return {"error": "Internal Server Error"}, 500



# Edit post on a thread - EDIT - /post/<int:post_id>/threads/<int:thread_id>
@posts_bp.route("/<int:post_id>/threads/<int:thread_id>", methods=["PUT", "PATCH"])
@jwt_required()
@auth_user_action(Post, "post_id")
def update_post_in_thread(thread_id, post_id):
    """
    Updates an existing post in a specific thread.

    Validates the request body data, updates the Post record with the specified ID within the given thread, and commits the changes to the database.

    Args:
        thread_id (int): The ID of the thread containing the post.
        post_id (int): The ID of the post to update.

    Returns:
        JSON: Serialised updated post with a 200 OK status if update is successful.
        JSON: Error message with a 404 Not Found status ifthe post is not found within the thread.
        JSON: Error message with a 400 Bad Request status if the request body is invalid.
        JSON: Error message with a 500 Internal Server Error status if an exception occurs.
    """
    try:
        # Load and validate the request data, allowing partial updates.
        body_data = post_schema.load(request.get_json(), partial=True)
        # Query to select the post by thread ID and post ID.
        stmt = db.select(Post).filter_by(id=post_id, thread_id=thread_id)
        post = db.session.scalar(stmt)

        if not post:
            return {"error": f"Post with ID {post_id} not found in Thread with ID {thread_id}."}, 404
        
        # Update post fields with new values from the request data.
        post.body = body_data.get("body", post.body)
        if body_data.get("timestamp"):
            post.timestamp = datetime.strptime(body_data["timestamp"], "%Y-%m-%d").date()
        
        # Commit the changes to the database.
        db.session.commit()

        return post_schema.dump(post), 200
    
    except ValidationError as e:
        return {"error": e.messages}, 400
    
    except Exception as e:
        db.session.rollback()
        return {"error": "Internal Server Error."}, 500
    


# Delete post in thread - DELETE - /post/<int:post_id>/threads/<int:thread_id>
@posts_bp.route("/<int:post_id>/threads/<int:thread_id>", methods=["DELETE"])
@jwt_required()
@auth_user_action(Post, "post_id")
def delete_post_in_thread(thread_id, post_id):
    """
    Deletes a post in a specific thread.

    Removes the Post record with the specified ID from the specified thread, along with all associated likes and comments.

    Args:
        thread_id (int): The ID of the thread containing the post.
        post_id (int): The Id of the post to delete.

    Returns:
        JSON: Success message with a 200 OK status if deletion is successful.
        JSON: Error message with a 404 Not Found status if the post is not found within the thread.
        JSON: Error message with a 500 Internal Server Error status if an exception occurs.
    """
    try:
        # Query to select the post by the thread ID and the post ID.
        stmt = db.select(Post).filter_by(id=post_id, thread_id=thread_id)
        post = db.session.scalar(stmt)

        if not post:
            return {"error": f"Post with ID {post_id} not found in Thread with ID {thread_id}."}, 404
        
        # Deleted associated likes and comments.
        db.session.query(Like).filter_by(post_id=post_id).delete()
        db.session.query(Comment).filter_by(post_id=post_id).delete()

        # Delete the post and commit the changes.
        db.session.delete(post)
        db.session.commit()

        return {"message": f"Post with ID {post_id} deleted successfully."}, 200
    
    except Exception as e:
        db.session.rollback()
        print(e)
        return {"error": "Internal Server Error."}, 500