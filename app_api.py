import random
import string
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException, Header, Depends
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

        # Error handling if no subjects are found
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

        # Convert ObjectId to string (if needed)
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
            response_data[board_name] = {}

            for medium in mediums:
                medium_name = medium["medium_name"]
                medium_id = str(medium["medium_id"])
                response_data[board_name][medium_name] = {}

                for cls in classes:
                    class_name = f"Class {cls['classs_name']}"
                    class_id = str(cls["classs_id"])

                    # Filter subjects for this specific board, medium, and class
                    filtered_subjects = [
                        subject["subject_name"]
                        for subject in subjects
                        if subject["board_id"] == board_id
                        and subject["medium_id"] == medium_id
                        and subject["class_id"] == class_id
                    ]

                    # Add subjects under the class if any exist
                    if filtered_subjects:
                        response_data[board_name][medium_name][class_name] = filtered_subjects

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
    
