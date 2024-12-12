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

# Helper functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

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
        logger.info(f"Login successful for user_id: {data.user_id}")
        return JSONResponse(content=response, status_code=200)
    else:
        logger.warning(f"Login attempt failed for user_id: {data.user_id}")
        raise HTTPException(status_code=404, detail="User not found")

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

@app.on_event("startup")
async def startup_db_client():
    global client
    client = AsyncIOMotorClient(MONGO_DETAILS)
    logger.info("MongoDB client initialized.")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    logger.info("MongoDB client closed.")
