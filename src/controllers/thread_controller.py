from datetime import datetime

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from utils import auth_thread_action

from init import db
from models.thread import InnovationThread, thread_schema, threads_schema
from models.post import Post


thread_bp = Blueprint("threads", __name__, url_prefix="/threads")


# Fetch all threads - GET - /thread
@thread_bp.route("/", methods=["GET"])
def get_all_threads():
    """
    Retrieves all threads from the database, ordered by timestamp in descending order.

    Queries the database for all InnovationThread records, orders them by timestamp in descending order, and returns the serlialised list of threads.

    Returns:
        JSON: Serialised lists of all threads with a 200 OK status if threads exist.
        JSON: Error message with a 404 Not Found status if no threads are found.
    """
    stmt = db.select(InnovationThread).order_by(InnovationThread.timestamp.desc())
    threads = db.session.scalars(stmt)
    
    if threads:
        return threads_schema.dump(threads), 200
    else:
        return {"error": "No threads found."}, 404


# Fetch a single thread - GET - /thread/<int:thread_id>
@thread_bp.route("/<int:thread_id>", methods=["GET"])
def get_single_thread(thread_id):
    """
    Retrieve a single thread by its ID.

    Queries the database for an InnovationThread record with the specified ID and returns the serialised thread.

    Args:
        thread_id (int): The ID of the thread to retrieve.
    
    Returns:
        JSON: Serialised thread with a 200 OK status if the thread exists.
        JSON: Error message with a 404 Not Found status if the thread is not found.
    """
    stmt = db.select(InnovationThread).filter_by(id=thread_id)
    thread = db.session.scalar(stmt)

    if thread:
        return thread_schema.dump(thread), 200
    else:
        return {"error": f"Thread with ID {thread_id} not found."}, 404



# Create a thread - POST - /threads
@thread_bp.route("/", methods=["POST"])
@jwt_required()
def create_thread():
    """
    Creates a new thread.

    Validates the request body data, creates a new InnovationThread record with the provided data, and stores it in the database.

    Returns:
        JSON: Serialised new thread with a 201 Created status if creation is successful.
        JSON: Error message with a 400 Bad Request status if the request body is invalid.
        JSON: Error message with a 500 Internal Server Error status if an excpetion occurs.
    """
    try:
        body_data = thread_schema.load(request.get_json())

        if not body_data or not isinstance(body_data.get("title"), str) or not body_data.get("title").strip():
            return {"error": "Invalid request title"}, 400
        
        new_thread = InnovationThread(
            title=body_data.get("title"),
            content=body_data.get("content"),
            timestamp=datetime.now(),
            user_id=get_jwt_identity()
        )
        db.session.add(new_thread)
        db.session.commit()

        return thread_schema.dump(new_thread), 201
    
    except ValidationError as err:
        return {"error": str(err)}, 400
    
    except Exception:
        db.session.rollback()
        return {"error": "Internal Server Error."}, 500
    


# Edit a thread - PUT, PATCH - /thread/<int:thread_id>
@thread_bp.route("/<int:thread_id>", methods=["PUT", "PATCH"])
@jwt_required()
@auth_thread_action
def edit_thread(thread_id):
    """
    Updates an existing thread by its ID.

    Validates the request body data, updates the InnovationThread record with the specified ID, and commits the changes to the database.

    Args:
        thread_id (int): The ID of the thread to update.

    Returns:
        JSON: Serialised updated thread with a 200 OK status if update is successful.
        JSON: Error message with a 404 Not Found status is the thread is not found.
        JSON: Error message with a 400 Bad Request status if the request body is invalid.
        JSON: Error message with a 500 Internal Server Error status if an unexpected excpetion occurs.
    """
    try:
        body_data = thread_schema.load(request.get_json(), partial=True)
        stmt = db.select(InnovationThread).filter_by(id=thread_id)
        thread = db.session.scalar(stmt)

        if not thread:
            return {"error": f"Thread with ID {thread_id} not found."}, 404
        
        if not body_data or not isinstance(body_data.get("title"), str) or not body_data.get("title").strip():
            return {"error": "Invalid request title."}, 400
        
        thread.title = body_data.get("title", thread.title)
        thread.content = body_data.get("content", thread.content)
        if body_data.get("timestamp"):
            thread.timestamp = datetime.strptime(body_data["timestamp"], "%Y-%m-%d %H:%M:%S")
        
        db.session.commit()

        return thread_schema.dump(thread), 200

    except ValidationError as err:
        return {"error": err.messages}, 400
    
    except Exception:
        db.session.rollback()
        return {"error": "Internal Server Error."}, 500
    


# Delete a thread - DELETE - /thread/<int:thread_id>
@thread_bp.route("/<int:thread_id>", methods=["DELETE"])
@jwt_required()
@auth_thread_action
def delete_thread(thread_id):
    """
    Deleted a thread by its ID.

    Removes the InnovationThread record witht the specified ID from the database, along with associated posts.

    Args:
        thread_id (int): The Id of the thread to delete.
    
    Returns:
        JSON: Success message with a 200 OK status if deletion is successful.
        JSON: Error message with a 404 Not Found status if the thread is not found.
        JSON: Error message with a 500 Internal Server Error status if an exception occurs.
    """
    try:
        thread = InnovationThread.query.get(thread_id)

        if not thread:
            return {"error": f"Thread with ID {thread_id} not found."}, 404
        
        db.session.query(Post).filter_by(thread_id=thread_id).delete()

        db.session.delete(thread)
        db.session.commit()

        return {"message": f"Thread with ID {thread_id} deleted successfully."}, 200
    
    except Exception:
        db.session.rollback()
        return {"error": "Internal Server Error."}, 500
    

