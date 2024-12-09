import random
import string
from typing import Dict, List, Optional, Tuple
from urllib import request
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query, Request, Body, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse, RedirectResponse
from pymongo.collection import Collection
from pymongo  import DESCENDING
from fastapi.staticfiles import StaticFiles
from passlib.context import CryptContext
from pydantic import BaseModel
# from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from docx import Document
import fitz  # PyMuPDF
import io
import os
import shutil
import re
import uuid
import random
from datetime import datetime
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from jose import jwt, JWTError
from datetime import datetime, timedelta
import bcrypt

app = FastAPI()

# Plain password
password = "password123".encode("utf-8")

# Generate a bcrypt hash
hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
print("Hashed Password:", hashed_password)

# Verify the password
is_valid = bcrypt.checkpw(password, hashed_password)
print("Password is Valid:", is_valid)

MONGO_DETAILS = "mongodb+srv://i-campus:atsiCampus123@cluster0.2q7k67a.mongodb.net/"
client = AsyncIOMotorClient(MONGO_DETAILS)
# database = client.State_Board
db = client['user_database']
# files_collection = database.get_collection("question_database")

# Mock Database
# auth_collection = {
#     "admin@example.com": {
#         "role_id": 1,
#         "password": "$2b$12$itqLIMkvRVvNje/H95OvHu5uFLpcw.DI63bpJkNwUnFnb6ic529de",  # Hashed "password123"
#     }
# }
# Collections for user data and authentication
profiles_collection = db['user_profiles']
auth_collection = db['user_auth']
board_collection = db['board']
medium_collection = db['medium']
institute_collection = db['institute']
class_collection = db['class']
subject_collection = db['subject']
topic_collection = db['topic']

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("exp") < datetime.utcnow().timestamp():
            raise HTTPException(status_code=401, detail="Token expired")
        return payload
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid token")



@app.get("/", response_class=HTMLResponse)
async def get_form():
    print("This is collection1")
    with open("static/login.html") as f:
        return f.read()
    
@app.get("/output", response_class=HTMLResponse)
async def get_form():
    with open("static/output.html") as f:
        return f.read()

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

class LoginData(BaseModel):
    email: str

@app.post("/all-login")
async def admin_login(data: LoginData):
    # Find the user by email in the 'user_auth' collection
    user_auth = await auth_collection.find_one({"email": data.email})
    
    if user_auth:
        # Generate an access token after finding the user
        access_token = create_access_token({"sub": data.email})
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        raise HTTPException(status_code=404, detail="User not found")



@app.get("/secure-data")
async def secure_data(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=403, detail="Missing or invalid token")
    token = authorization.split(" ")[1]
    user_data = verify_token(token)
    return {"message": "Access granted", "user": user_data["sub"]}
