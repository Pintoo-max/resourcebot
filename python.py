from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from pymongo import MongoClient
from fastapi.staticfiles import StaticFiles
from passlib.context import CryptContext

app = FastAPI()

client = MongoClient("mongodb+srv://i-campus:atsiCampus123@cluster0.2q7k67a.mongodb.net/")
db = client['user_database']

# Collections for user data and authentication
profiles_collection = db['user_profiles']
auth_collection = db['user_auth']

app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize CryptContext for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(BaseModel):
    role: str
    name: str
    surname: str
    institute_name: str
    class_name: str
    institute_id: str
    date_of_birth: str
    email: str
    password: str

def get_role_id(role: str):
    """Assign role_id based on the user's role."""
    if role == "admin":
        return 1
    elif role == "teacher":
        return 2
    elif role == "student":
        return 3
    else:
        raise ValueError("Invalid role")

@app.get("/", response_class=HTMLResponse)
async def get_form():
    with open("static/register.html", 'rb') as f:
        content = f.read()
        return content.decode('utf-8')

@app.post("/register")
async def register_user(user: User):
    hashed_password = pwd_context.hash(user.password)
    
    # Assign role_id based on the role
    role_id = get_role_id(user.role)
    
    # Create user profile data
    user_profile = {
        "role": user.role,
        "name": user.name,
        "surname": user.surname,
        "institute_name": user.institute_name,
        "class_name": user.class_name,
        "institute_id": user.institute_id,
        "date_of_birth": user.date_of_birth,
        "email": user.email
    }

    # Create auth data
    auth_data = {
        "role": user.role,
        "email": user.email,
        "password": hashed_password,
        "role_id": role_id  # Store the role_id
    }

    # Check if the email is already registered
    if auth_collection.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="User already registered")

    # Insert data into both collections
    profiles_collection.insert_one(user_profile)
    auth_collection.insert_one(auth_data)

    return {"message": "Registration successful"}

class LoginData(BaseModel):
    email: str
    password: str
    role_id: int

class StudentTeacherLoginData(BaseModel):
    email: str
    role_id: int
    password: str

@app.post("/student-teacher-login")
async def student_teacher_login(data: StudentTeacherLoginData):
    # Query to find user in auth collection by email and role_id
   
    user_auth = auth_collection.find_one({"email": data.email, "role_id": data.role_id})

    if user_auth:
        # Verify the entered password against the stored hashed password
        if pwd_context.verify(data.password, user_auth['password']):
            return {"message": "Login successful"}
        else:
            raise HTTPException(status_code=401, detail="Incorrect password")
    else:
        return {"message": "User not found. Please register first."}

    

@app.post("/admin-login")
async def admin_login(data: LoginData):
   

    # Query to find user in auth collection by email and role_id
   
    user_auth = auth_collection.find_one({"email": data.email, "role_id": data.role_id})

    if user_auth:
            # Verify the entered password against the stored hashed password
            if pwd_context.verify(data.password, user_auth['password']):
                return {"message": "Login successful"}
            else:
                raise HTTPException(status_code=401, detail="Incorrect password")
    else:
            return {"message": "User not found. Please register first."}
        


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
