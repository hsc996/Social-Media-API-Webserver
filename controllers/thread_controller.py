from datetime import datetime

from init import db
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.thread import InnovationThread, thread_schema, threads_schema
from models.post import Post
from marshmallow import ValidationError


thread_bp = Blueprint("threads", __name__, url_prefix="/threads")



# Fetch all threads - GET - /thread
@thread_bp.route("/", methods=["GET"])
def get_all_threads():
    stmt = db.select(InnovationThread).order_by(InnovationThread.timestamp.desc())
    threads = db.session.scalars(stmt)
    
    return threads_schema.dump(threads), 200


# Fetch a single thread - GET - /thread/<int:thread_id>
@thread_bp.route("/<int:thread_id>", methods=["GET"])
def get_single_thread(thread_id):
    stmt = db.select(InnovationThread).filter_by(id=thread_id)
    thread = db.session.scalar(stmt)

    if thread is None:
        return {"error": f"Thread with ID {thread_id} not found."}, 404
    
    return thread_schema.dump(thread), 200



# Create a thread - POST - /thread
@thread_bp.route("/", methods=["POST"])
@jwt_required()
def create_thread():
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

        return {"message": "Thread created successfully", "thread_id": new_thread.id}, 201
    
    except ValidationError as e:
        return {"error": str(e)}, 400
    
    except Exception as e:
        db.session.rollback()
        return {"error": "Internal Server Error."}, 500
    


# Edit a thread - PUT, PATCH - /thread/<int:thread_id>
@thread_bp.route("/<int:thread_id>", methods=["PUT", "PATCH"])
@jwt_required()
def edit_thread(thread_id):
    try:
        body_data = thread_schema.load(request.get_json(), partial=True)
        stmt = db.select(InnovationThread).filter_by(id=thread_id)
        thread = db.session.scalar(stmt)

        if not thread:
            return {"error": f"Thread with ID {thread_id} not found."}, 404
        
        thread.title = body_data.get("title", thread.title)
        thread.content = body_data.get("content", thread.content)
        if body_data.get("timestamp"):
            thread.timestamp = datetime.strptime(body_data["timestamp"], "%Y-%m-%d %H:%M:%S")
        
        db.session.commit()

        return thread_schema.dump(thread), 200

    except ValidationError as e:
        return {"error": e.messages}, 400
    
    except Exception as e:
        db.session.rollback()
        return {"error": "Internal Server Error."}, 500
    


# Delete a thread - DELETE - /thread/<int:thread_id>
@thread_bp.route("/<int:thread_id>", methods=["DELETE"])
@jwt_required()
def delete_thread(thread_id):
    try:
        thread = InnovationThread.query.get(thread_id)

        if not thread:
            return {"error": f"Thread with ID {thread_id} not found."}, 404
        
        db.session.query(Post).filter_by(thread_id=thread_id).delete()

        db.session.delete(thread)
        db.session.commit()

        return {"message": f"Thread with ID {thread_id} deleted successfully."}, 200
    
    except Exception as e:
        db.session.rollback()
        return {"error": "Internal Server Error."}, 500
    

