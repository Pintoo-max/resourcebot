import random
import string
from typing import Dict, Optional, List
from fastapi import FastAPI, HTTPException, Header, Depends, Body
from fastapi.responses import HTMLResponse, JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from bson import ObjectId 
import logging
from dotenv import load_dotenv
import os

from pymongo.collection import Collection
# Load environment variables
load_dotenv()

# Constants and configurations
MONGO_DETAILS = os.getenv("MONGO_DETAILS", "mongodb+srv://i-campus:atsiCampus123@cluster0.2q7k67a.mongodb.net/")
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# MongoDB client and database
client = AsyncIOMotorClient(MONGO_DETAILS)
db = client['user_database']
profiles_collection = db['user_profiles']
auth_collection = db['user_auth']
board_collection = db['board']
tokens_collection = db["access_tokens"] 
medium_collection = db['medium']
institute_collection = db['institute']
class_collection = db['class']
subject_collection = db['subject']
topic_collection = db['topic']
# Helper functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

async def save_token_to_db(user_id: str, token: str):
    expiration_time = datetime.utcnow() + timedelta(hours=1)  # Token valid for 1 hour
    token_data = {
        "user_id": user_id,
        "access_token": token,
        "expires_at": expiration_time,
        "created_at": datetime.utcnow()
    }
    await tokens_collection.insert_one(token_data)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid token")

# Helper function to convert ObjectId to string
def convert_objectid_to_str(item):
    if isinstance(item, ObjectId):
        return str(item)
    if isinstance(item, dict):
        return {key: convert_objectid_to_str(value) for key, value in item.items()}
    if isinstance(item, list):
        return [convert_objectid_to_str(element) for element in item]
    return item

# Pydantic models
class LoginData(BaseModel):
    user_id: str

# Routes
@app.get("/", response_class=HTMLResponse)
async def get_form():
    with open("static/login.html") as f:
        return f.read()

@app.post("/all-login")
async def admin_login(data: LoginData):
    # Find the user by user_id in the 'user_auth' collection
    user_auth = await auth_collection.find_one({"email": data.user_id})  # Assuming user_id matches email field

    if user_auth:
        # Generate an access token
        access_token = create_access_token({"sub": user_auth["email"]})  # Use email for the token subject
        response = {
            "status": 200,
            "message": "Request Successful",
            "data": {
                "access_token": access_token,
                "token_type": "bearer"
            }
        }
        await save_token_to_db(user_auth["email"], access_token)
        logger.info(f"Login successful for user_id: {data.user_id}")
        return JSONResponse(content=response, status_code=200)
    else:

        response1 = {
            "status": 404,
            "message": "User not found",
            "data": {
                "access_token": "none",
                "token_type": "none"
            }
        }
        logger.warning(f"Login attempt failed for user_id: {data.user_id}")
        raise HTTPException(status_code=404, detail=response1)

@app.get("/secure-data")
async def secure_data(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=403, detail="Missing or invalid token")
    token = authorization.split(" ")[1]
    try:
        user_data = verify_token(token)
        return {"message": "Access granted", "user": user_data["sub"]}
    except HTTPException as e:
        logger.error(f"Token error: {e.detail}")
        raise

@app.post("/all-board")
async def get_board(data: LoginData):
    # Find the user by user_id in the 'user_auth' collection
    user_auth = await auth_collection.find_one({"email": data.user_id})  # Assuming user_id matches email field

    if user_auth:
        # Generate an access token
        access_token = create_access_token({"sub": user_auth["email"]})  # Use email for the token subject
        response = {
            "status": 200,
            "message": "Request Successful",
            "data": {
                "access_token": access_token,
                "token_type": "bearer"
            }
        }
        logger.info(f"Login successful for user_id: {data.user_id}")
        return JSONResponse(content=response, status_code=200)
    else:

        response1 = {
            "status": 404,
            "message": "User not found",
            "data": {
                "access_token": "none",
                "token_type": "none"
            }
        }
        logger.warning(f"Login attempt failed for user_id: {data.user_id}")
        raise HTTPException(status_code=404, detail=response1)

async def verify_access_token(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")
    
    token = authorization.split(" ")[1]
    token_record = await tokens_collection.find_one({"access_token": token})
    if not token_record:
        raise HTTPException(status_code=401, detail="Token not found or invalid")
    
    # Check if the token has expired
    if token_record["expires_at"] < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Token has expired")


    # Replace "your_valid_token" with the actual validation logic or token    
    return {"user": "authenticated_user"}  # Mock user details

mock_board_data = [
    {"id": 1, "name": "Science Board"},
    {"id": 2, "name": "Mathematics Board"}
]

@app.get("/boards")
async def get_boards(user: dict = Depends(verify_access_token)):
    boards = await board_collection.find().to_list(length=100)  # Adjust length as needed
    medium = await medium_collection.find().to_list(length=100)  # Adjust length as needed
    if not boards:
        raise HTTPException(status_code=404, detail="No boards found")

    boards = convert_objectid_to_str(boards)
    return {
        "status": 200,
        "message": "Boards fetched successfully",
        "data": boards
    }

@app.get("/all-master")
async def get_boards(user: dict = Depends(verify_access_token)):
    try:
        boards = await board_collection.find().to_list(length=100)  # Fetch all boards
        mediums = await medium_collection.find().to_list(length=100)  # Fetch all mediums
        classes = await class_collection.find().to_list(length=100)  # Fetch all classes
        subjects = await subject_collection.find().to_list(length=100)  # Fetch all subjects

        # Error handling if no data is found
        if not boards or not mediums or not classes or not subjects:
            response1 = {
                "status": 404,
                "message": "Data not found",
                "data": {
                    "access_token": "none",
                    "token_type": "none"
                }
            }
            logger.warning("No data found for boards, mediums, classes, or subjects")
            raise HTTPException(status_code=404, detail=response1)

        # Convert ObjectId to string
        boards = convert_objectid_to_str(boards)
        mediums = convert_objectid_to_str(mediums)
        classes = convert_objectid_to_str(classes)
        subjects = convert_objectid_to_str(subjects)

        # Response structure
        response_data = {"Category": ["AI generated worksheet", "Textbook", "Syllabus", "Previous Year Questions"]}

        # Organize data by board, medium, and class using subject_collection as the link
        for board in boards:
            board_name = board["board_name"]
            board_id = str(board["board_id"])
            response_data[board_name] = {
                "id": board_id,
                "mediums": {}
            }

            for medium in mediums:
                medium_name = medium["medium_name"]
                medium_id = str(medium["medium_id"])
                response_data[board_name]["mediums"][medium_name] = {
                    "id": medium_id,
                    "classes": {}
                }

                for cls in classes:
                    class_name = f"Class {cls['classs_name']}"
                    class_id = str(cls["classs_id"])
                    response_data[board_name]["mediums"][medium_name]["classes"][class_name] = {
                        "id": class_id,
                        "subjects": []
                    }

                    # Filter subjects for this specific board, medium, and class
                    filtered_subjects = [
                        {"id": str(subject["subject_id"]), "name": subject["subject_name"]}
                        for subject in subjects
                        if subject["board_id"] == board_id
                        and subject["medium_id"] == medium_id
                        and subject["class_id"] == class_id
                    ]

                    # Add subjects under the class if any exist
                    if filtered_subjects:
                        response_data[board_name]["mediums"][medium_name]["classes"][class_name]["subjects"] = filtered_subjects

        return {
            "status": 200,
            "message": "Request Successful",
            "data": response_data
        }

    except Exception as e:
        response1 = {
            "status": 500,
            "message": "Internal Server Error",
            "data": {
                "access_token": "none",
                "token_type": "none"
            }
        }
        logger.error(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=response1)
    
@app.on_event("startup")
async def startup_db_client():
    global client
    client = AsyncIOMotorClient(MONGO_DETAILS)
    logger.info("MongoDB client initialized.")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    logger.info("MongoDB client closed.")
    
#worksheet data


async def get_or_create_database(board_name: str):
    # Get the list of existing databases
    existing_databases = await client.list_database_names()
    
    # Check if the selected board's database already exists
    if board_name in existing_databases:
        db = client[board_name]
        print(f"Using existing database: '{board_name}'")
    else:
        # Create the new database if it does not exist
        db = client[board_name]
        print(f"Created new database: '{board_name}'")
    
    return db

async def get_collection(board_name: str, class_name: str) -> Collection:
    collection_name = f"class_{class_name}"
    print(f"Accessing collection: {collection_name} in database: {board_name}")

    # Get or create the database
    db = await get_or_create_database(board_name)

    # Get the collection from the database
    collection = db[collection_name]
    
    return collection

# Define the request model
class QuestionRequest(BaseModel):
    board: int
    medium: int
    grade: int
    subject: int
    lesson: int
    tasks: List[str]
    limit: Optional[int] = None  # Limit is optional, default is None
    

@app.post("/get_questions_and_answers_api_one")
async def get_questions_and_answers_api(request: QuestionRequest):
    # Validate the limit
    if request.limit is not None and request.limit < 1:
        raise HTTPException(status_code=422, detail="Limit must be at least 1")

    # Get the board and grade information
    existing_board = await board_collection.find_one({"board_id": request.board})
    if not existing_board:
        raise HTTPException(status_code=404, detail="Board not found")
    board_name = existing_board["board_name"]

    existing_grade = await class_collection.find_one({"classs_id": request.grade})
    if not existing_grade:
        raise HTTPException(status_code=404, detail="Grade not found")
    class_name = existing_grade["classs_name"]

    # Construct the query to find the lesson and subject
    query = {
        "board": str(request.board),
        "medium": str(request.medium),
        "grade": str(request.grade),
        "subject": str(request.subject),
        "lesson": str(request.lesson),
        "tasks": {"$in": request.tasks}  # Handle multiple tasks
    }

    # Get the database and collection
    db = await get_or_create_database(board_name)
    collection = await get_collection(board_name, class_name)
    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Fetch the document
    document = await collection.find_one(query)
    if not document:
        return {
            "status": 404,
            "message": "No data found for the specified criteria",
            "data": {}
        }

    # Process the data
    questions_and_answers = document.get("questions_and_answers", {})
    result = []

    # Loop over each task type in the request
    for task in request.tasks:
        # Process each question based on task
        for i in range(1, 26):  # Assuming 25 questions max
            question_key = f"question{i}"
            answer_key = f"answer{i}"

            # If the question and answer exist for this task, add them
            if question_key in questions_and_answers and answer_key in questions_and_answers:
                question_data = {
                    "question": questions_and_answers.get(question_key, ""),
                    "type": task,
                    "correct_answer": questions_and_answers.get(answer_key, "")
                }

                # Add task-specific fields for different task types
                if task == "multiple-choice-questions":
                    question_data["options"] = questions_and_answers.get(f"options{i}", [])
                elif task == "true-false":
                    question_data["options"] = ["True", "False"]
                elif task == "match-the-column":
                    question_data["options"] = {
                        "column_a": questions_and_answers.get(f"column_a{i}", []),
                        "column_b": questions_and_answers.get(f"column_b{i}", [])
                    }
                elif task == "fill-in-the-blanks":
                    # No options for fill-in-the-blanks, just the correct answer
                    pass

                result.append(question_data)

    # Apply the limit if provided
    if request.limit:
        result = result[:request.limit]

    # Return the response
    return {
        "status": 200,
        "message": "Worksheet generated successfully",
        "data": {
            "questions": result
        }
    }
    

# Define the request model
class TaskRequest(BaseModel):
    type: str
    limit: Optional[int] = 25  # Default limit is 25 if not provided

class QuestionRequest(BaseModel):
    board: int
    medium: int
    grade: int
    subject: int
    lesson: int
    tasks: List[TaskRequest]  # Accept a list of TaskRequest objects
    limit: Optional[int] = 10  # Global limit (optional)

@app.post("/get_questions_and_answers_api")
async def get_questions_and_answers_api(request: QuestionRequest):
    # Validate the limit for each task
    for task in request.tasks:
        if task.limit is not None and task.limit < 1:
            raise HTTPException(status_code=422, detail="Limit must be at least 1")

    # Get the board and grade information
    existing_board = await board_collection.find_one({"board_id": request.board})
    if not existing_board:
        raise HTTPException(status_code=404, detail="Board not found")
    board_name = existing_board["board_name"]

    existing_grade = await class_collection.find_one({"classs_id": request.grade})
    if not existing_grade:
        raise HTTPException(status_code=404, detail="Grade not found")
    class_name = existing_grade["classs_name"]

    # Get the database and collection
    db = await get_or_create_database(board_name)
    collection = await get_collection(board_name, class_name)
    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    final_result = []  # Store the questions for all tasks here

    # Loop over each task type in the request
    for task_info in request.tasks:
        task = task_info.type  # The task type (e.g., "true-false")
        task_limit = task_info.limit  # Task-specific limit

        # Construct the query for the specific task
        task_query = {
            "board": str(request.board),
            "medium": str(request.medium),
            "grade": str(request.grade),
            "subject": str(request.subject),
            "lesson": str(request.lesson),
            "tasks": task  # Filter by the specific task
        }

        # Fetch the document for this specific task
        document = await collection.find_one(task_query)
        if not document:
            continue  # Skip if no data is found for this task

        # Process the questions and answers for this task
        questions_and_answers = document.get("questions_and_answers", {})
        task_result = []  # Store the questions for this specific task

        # Loop over each question for this task (assuming up to 25 questions)
        for i in range(1, 26):
            question_key = f"question{i}"
            answer_key = f"answer{i}"

            # If the question and answer exist for this task, add them
            if question_key in questions_and_answers and answer_key in questions_and_answers:
                question_data = {
                    "question": questions_and_answers.get(question_key, ""),
                    "type": task,
                    "correct_answer": questions_and_answers.get(answer_key, "")
                }

                # Add task-specific fields for different task types
                if task == "multiple-choice-questions":
                    question_data["options"] = questions_and_answers.get(f"options{i}", [])
                elif task == "true-false":
                    question_data["options"] = ["True", "False"]
                elif task == "match-the-column":
                    question_data["options"] = {
                        "column_a": questions_and_answers.get(f"column_a{i}", []),
                        "column_b": questions_and_answers.get(f"column_b{i}", [])
                    }
                elif task == "fill-in-the-blanks":
                    # No options for fill-in-the-blanks, just the correct answer
                    pass

                task_result.append(question_data)

                # If we have reached the task-specific limit, stop adding questions for this task
                if len(task_result) >= task_limit:
                    break

        # Add task-specific result to the final result
        final_result.extend(task_result)

        # If we have reached the global limit, stop processing further tasks
        if len(final_result) >= request.limit:
            break

    # Return the response
    return {
        "status": 200,
        "message": "Worksheet generated successfully",
        "data": {
            "questions": final_result
        }
    }


@app.post("/get_syllabus")
async def get_syllabus(
    payload: dict = Body(...)
):
    # Extract parameters from the JSON payload
    board = payload.get("board")
    medium = payload.get("medium")
    grade = payload.get("grade")
    subject = payload.get("subject")
    tasks = payload.get("tasks")

    # Construct the query
    query = {
        "board": board,
        "medium": medium,
        "grade": grade,
        "subject": subject,
        "tasks": tasks
    }

    print("Query:", query)

    # Retrieve board information
    existing_board = await board_collection.find_one({"board_id": int(board)})
    if not existing_board:
        raise HTTPException(status_code=404, detail="Board not found")
    board_name = existing_board["board_name"]

    # Retrieve grade information
    existing_grade = await class_collection.find_one({"classs_id": int(grade)})
    if not existing_grade:
        raise HTTPException(status_code=404, detail="Grade not found")
    class_name = existing_grade["classs_name"]

    # Get or create the database and collection
    db = await get_or_create_database(board_name)
    print("This is db", db)

    collection = await get_collection(board_name, class_name)
    print("This is collection", collection)

    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Find the document based on the query
    document = await collection.find_one(query)
    if not document:
        print("No document found for query")
        raise HTTPException(status_code=404, detail="No data found for the specified criteria")
    else:
        document['_id'] = str(document['_id'])

    # Update the file_path to include your domain
    if "file_path" in document:
        base_url = "https://learnaize.com/static/"
        document["file_path"] = base_url + document["file_path"].replace("\\", "/")

    return {
        "status": 200,
        "message": "Syllabus pdf extracted successfully",
        "data": document
        }


@app.post("/get_textbook-solution")
async def get_textbook_solution(
    payload: dict = Body(...)
):
    # Extract parameters from the JSON payload
    board = payload.get("board")
    medium = payload.get("medium")
    grade = payload.get("grade")
    subject = payload.get("subject")
    lesson = payload.get("lesson")
    tasks = payload.get("tasks")

    # Construct the query
    query = {
        "board": board,
        "medium": medium,
        "grade": grade,
        "subject": subject,
        "lesson": lesson,
        "tasks": tasks
    }

    print("Query:", query)

    # Retrieve board information
    existing_board = await board_collection.find_one({"board_id": int(board)})
    if not existing_board:
        raise HTTPException(status_code=404, detail="Board not found")
    board_name = existing_board["board_name"]

    # Retrieve grade information
    existing_grade = await class_collection.find_one({"classs_id": int(grade)})
    if not existing_grade:
        raise HTTPException(status_code=404, detail="Grade not found")
    class_name = existing_grade["classs_name"]

    # Get or create the database and collection
    db = await get_or_create_database(board_name)
    print("This is db", db)

    collection = await get_collection(board_name, class_name)
    print("This is collection", collection)

    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Find the document based on the query
    document = await collection.find_one(query)
    if not document:
        print("No document found for query")
        raise HTTPException(status_code=404, detail="No data found for the specified criteria")
    else:
        document['_id'] = str(document['_id'])

    # Update the file_path to include your domain
    if "file_path" in document:
        base_url = "https://learnaize.com/static/"
        document["file_path"] = base_url + document["file_path"].replace("\\", "/")

    return {
        "status": 200,
        "message": "Text-Book-Solution pdf extracted successfully",
        "data": document
        }


@app.post("/get_SamplePaper-solution")
async def get_SamplePaper_solution(
    payload: dict = Body(...)
):
    # Extract parameters from the JSON payload
    board = payload.get("board")
    medium = payload.get("medium")
    grade = payload.get("grade")
    subject = payload.get("subject")
    # lesson = payload.get("lesson")
    tasks = payload.get("tasks")

    # Construct the query
    query = {
        "board": board,
        "medium": medium,
        "grade": grade,
        "subject": subject,
        # "lesson": lesson,
        "tasks": tasks
    }

    print("Query:", query)

    # Retrieve board information
    existing_board = await board_collection.find_one({"board_id": int(board)})
    if not existing_board:
        raise HTTPException(status_code=404, detail="Board not found")
    board_name = existing_board["board_name"]

    # Retrieve grade information
    existing_grade = await class_collection.find_one({"classs_id": int(grade)})
    if not existing_grade:
        raise HTTPException(status_code=404, detail="Grade not found")
    class_name = existing_grade["classs_name"]

    # Get or create the database and collection
    db = await get_or_create_database(board_name)
    print("This is db", db)

    collection = await get_collection(board_name, class_name)
    print("This is collection", collection)

    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    documents = await collection.find(query).to_list(length=None)
    if not documents:
        print("No document found for query")
        raise HTTPException(status_code=404, detail="No data found for the specified criteria")
    else:
        # Convert `_id` fields to strings
        for doc in documents:
            doc['_id'] = str(doc['_id'])

        # Update the file_path for each document
        base_url = "https://learnaize.com/static/"
        for doc in documents:
            if "file_path" in doc:
                doc["file_path"] = base_url + doc["file_path"].replace("\\", "/")

    return {
        "status": 200,
        "message": "Sample Paper Solution pdf extracted successfully",
        "data": documents
    }


@app.post("/get_textBook")
async def get_textBook(
    payload: dict = Body(...)
):
    # Extract parameters from the JSON payload
    board = payload.get("board")
    medium = payload.get("medium")
    grade = payload.get("grade")
    # subject = payload.get("subject")
    # lesson = payload.get("lesson")
    tasks = payload.get("tasks")

    # Construct the query
    query = {
        "board": board,
        "medium": medium,
        "grade": grade,
        # "subject": subject,
        # "lesson": lesson,
        "tasks": tasks
    }

    print("Query:", query)

    # Retrieve board information
    existing_board = await board_collection.find_one({"board_id": int(board)})
    if not existing_board:
        raise HTTPException(status_code=404, detail="Board not found")
    board_name = existing_board["board_name"]

    # Retrieve grade information
    existing_grade = await class_collection.find_one({"classs_id": int(grade)})
    if not existing_grade:
        raise HTTPException(status_code=404, detail="Grade not found")
    class_name = existing_grade["classs_name"]

    # Get or create the database and collection
    db = await get_or_create_database(board_name)
    print("This is db", db)

    collection = await get_collection(board_name, class_name)
    print("This is collection", collection)

    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    documents = await collection.find(query).to_list(length=None)
    if not documents:
        print("No document found for query")
        raise HTTPException(status_code=404, detail="No data found for the specified criteria")
    else:
        # Convert `_id` fields to strings
        for doc in documents:
            doc['_id'] = str(doc['_id'])

        # Update the file_path for each document
        base_url = "https://learnaize.com/static/"
        for doc in documents:
            if "file_path" in doc:
                doc["file_path"] = base_url + doc["file_path"].replace("\\", "/")

    return {
        "status": 200,
        "message": "Text Book extracted successfully",
        "data": documents
    }

@app.post("/get_questionBank")
async def get_questionBank(
    payload: dict = Body(...)
):
    # Extract parameters from the JSON payload
    board = payload.get("board")
    medium = payload.get("medium")
    grade = payload.get("grade")
    subject = payload.get("subject")
    tasks = payload.get("tasks")

    # Construct the query
    query = {
        "board": board,
        "medium": medium,
        "grade": grade,
        "subject": subject,
        "tasks": tasks
    }

    print("Query:", query)

    # Retrieve board information
    existing_board = await board_collection.find_one({"board_id": int(board)})
    if not existing_board:
        raise HTTPException(status_code=404, detail="Board not found")
    board_name = existing_board["board_name"]

    # Retrieve grade information
    existing_grade = await class_collection.find_one({"classs_id": int(grade)})
    if not existing_grade:
        raise HTTPException(status_code=404, detail="Grade not found")
    class_name = existing_grade["classs_name"]

    # Get or create the database and collection
    db = await get_or_create_database(board_name)
    print("This is db", db)

    collection = await get_collection(board_name, class_name)
    print("This is collection", collection)

    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Find the document based on the query
    document = await collection.find_one(query)
    if not document:
        print("No document found for query")
        raise HTTPException(status_code=404, detail="No data found for the specified criteria")
    else:
        document['_id'] = str(document['_id'])

    # Update the file_path to include your domain
    if "file_path" in document:
        base_url = "https://learnaize.com/static/"
        document["file_path"] = base_url + document["file_path"].replace("\\", "/")

    return {
        "status": 200,
        "message": "Syllabus pdf extracted successfully",
        "data": document
        }