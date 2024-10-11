import random
from typing import Dict, List, Optional, Tuple
from urllib import request
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query, Request, Body
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
from datetime import datetime
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request


app = FastAPI()
# templates = Jinja2Templates(directory="templates") 

MONGO_DETAILS = "mongodb+srv://i-campus:atsiCampus123@cluster0.2q7k67a.mongodb.net/"
client = AsyncIOMotorClient(MONGO_DETAILS)
# database = client.State_Board
db = client['user_database']
# files_collection = database.get_collection("question_database")

# Collections for user data and authentication
profiles_collection = db['user_profiles']
auth_collection = db['user_auth']
board_collection = db['board']
medium_collection = db['medium']
institute_collection = db['institute']
class_collection = db['class']
subject_collection = db['subject']
topic_collection = db['topic']

# Secret key for signing sessions
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")

# def get_collection(class_name: str) -> Collection:
#     collection_name = f"class_{class_name}"
#     print(collection_name)
#     return database[collection_name]


app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/images", StaticFiles(directory="images"), name="images")

@app.get("/", response_class=HTMLResponse)
async def get_form():
    print("This is collection1")
    with open("static/login.html") as f:
        return f.read()
    
@app.get("/output", response_class=HTMLResponse)
async def get_form():
    with open("static/output.html") as f:
        return f.read()

@app.get("/register", response_class=HTMLResponse)
async def get_form():
    with open("static/register.html") as f:
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

@app.post("/submit")
async def form_uplaod(
    request: Request,  # Added request to access form data dynamically
    board: str = Form(...),
    medium: str = Form(...),
    grade: str = Form(...),
    subject: str = Form(...),
   # lesson: str = Form(...),
    tasks: str = Form(...),
    set_number: str = Form(None),  # Accept set number from form
    prev_years: str = Form(None),  # Accept set number from form
    file: UploadFile = File(...),
   ):
   
    print(board)
    print(medium)
    print("This is subject")
    
  
    if tasks=='text-book-solution':
        print(tasks)
        form_data = await request.form()
        lesson = form_data.get('lesson')  # Fetch lesson from form data dynamically
        unique_code = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        new_filename = f"{board}_{medium}_{grade}_{subject}_{lesson}_{tasks}"
        pdffilename = f"{board}_{medium}_{grade}_{subject}_{lesson}_{tasks}.pdf"
        print(new_filename)

        print("Generated filename:", pdffilename)

        # Ensure the upload folder exists
        upload_folder = 'static/upload/textbook_pdf'
        upload_folder1='upload/textbook_pdf'
        file_path = os.path.join(upload_folder, pdffilename)
        file_path1 = os.path.join(upload_folder1, pdffilename)
      # print("file path name", file_path)
       # file.save(file_path)

       # Save the file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        print("File uploaded successfully:", pdffilename)

        existing_grade = await class_collection.find_one({"classs_id": int(grade)})
        print(existing_grade)
        class_name = existing_grade["classs_name"]

        db = await get_or_create_database(board_name)
        print("This is db", db)

        # Get the collection using both the board name and class name
        collection = await get_collection(board_name, class_name)  # Pass both arguments
        print("This is collection", collection)

       # if file.content_type == 'application/pdf':  # If it's already a PDF
           # with open(file_path, "wb") as buffer:
               # shutil.copyfileobj(file.file, buffer)
           # print("File uploaded successfully as PDF:", pdffilename)
    
       # elif file.content_type == 'text/html':  # Example: Converting an HTML file to PDF
            # html_content = file.file.read().decode('utf-8')  # Read the HTML content
           # pdfkit.from_string(html_content, file_path)  # Convert HTML to PDF
           # print("HTML file converted and saved as PDF:", pdffilename)
        
        #else:
          #  print(f"Error: Unsupported file type '{file.content_type}'. Only PDF or HTML supported for conversion.")
       
        document = {
                "board": board,
                "medium": medium,
                "grade": grade,
                "subject": subject,
                "lesson": lesson,
                "filename": new_filename,
                "tasks": tasks,
                "unique_code": unique_code,
                "timestamp": timestamp,
                "file_path": file_path1
            }
        result = await collection.insert_one(document)
        print("Document to insert:", document)

        print("This is detect formatresult collection")
        print(result)
        # return {"file_id": str(result.inserted_id), "message": "File uploaded and saved successfully", "filename": new_filename}
        return {
                "status" : "1",
                "file_id": str(result.inserted_id), 
                "message": "File uploaded and saved successfully", 
                "filename": new_filename
        }

       

    elif tasks=='sample-paper-solution':
       # print(set_number)
        unique_code = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        new_filename = f"{board}_{medium}_{grade}_{subject}_{tasks}_{set_number}"
        pdffilename = f"{board}_{medium}_{grade}_{subject}_{tasks}_{set_number}.pdf"
        print(new_filename)

        print("Generated filename:", pdffilename)
        existing_grade = await class_collection.find_one({"classs_id": int(grade)})
        print(existing_grade)
        class_name = existing_grade["classs_name"]

        existing_board = await board_collection.find_one({"board_id": int(board)})
        print(existing_board)
        board_name = existing_board["board_name"]
        
        existing_medium = await medium_collection.find_one({"medium_id": int(medium) })
        print(existing_medium)
        medium_name = existing_medium["medium_name"]

        existing_subject = await subject_collection.find_one({"subject_id": int(subject) })
        print(existing_subject)
        subject_name = existing_subject["subject_name"]

        # collection = get_collection(class_name)
        # print(collection)

        db = await get_or_create_database(board_name)
        print("This is db", db)

        # Get the collection using both the board name and class name
        collection = await get_collection(board_name, class_name)  # Pass both arguments
        print("This is collection", collection)

        # Check for existing files with the same base filename
        existing_file = await collection.find_one({"filename": new_filename,"paper_year":prev_years})



        if existing_file:
            return {"status": "0", "message": "File already exsist"}
           # return "alredy exsist"
        else:


            # Ensure the upload folder exists
            upload_folder = 'static/upload/sample_papers'
            upload_folder1='upload/sample_papers'
            file_path = os.path.join(upload_folder, pdffilename)
            file_path1 = os.path.join(upload_folder1, pdffilename)
        # print("file path name", file_path)
        # file.save(file_path)

        # Save the file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            print("File uploaded successfully:", pdffilename)

            

            document = {
                     "board": board,
                     "board_name": board_name,
                     "medium": medium,
                     "medium_name": medium_name,
                     "grade": grade,
                     "grade_name": class_name,
                     "subject": subject,
                     "subject_name": subject_name,
                     "filename": new_filename,
                     "tasks": tasks,
                     "set_number":set_number,
                     "paper_year":prev_years,
                     "unique_code": unique_code,
                     "timestamp": timestamp,
                     "file_path": file_path1
                }
            result = await collection.insert_one(document)
            #print("Document to insert:", document)

            print("This is detect format result collection")
            print(result)
           # return {"status": "1", "message": "File uploaded successfully"}
            return {
                "status" : "1",
                "file_id": str(result.inserted_id), 
                "message": "File uploaded and saved successfully", 
                "filename": new_filename
                }


    else:
        # with open(filename, 'r') as file:
       # print("my documnet check")
        file_content = await file.read()
        file_extension = file.filename.split('.')[-1].lower()
       # print(file_extension)

        if file_extension == 'pdf':
            text = extract_text_from_pdf(file_content)
        elif file_extension in ['doc', 'docx']:
            text = extract_text_from_doc(file_content)
            #print(text)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")
       # print("come after file read")

        form_data = await request.form()
        lesson = form_data.get('lesson')  # Fetch lesson from form data dynamically
    # Preprocess the document into sections

        task_sections = preprocess_document(text)
    
    # Process each section and store in the appropriate collection
        for task_type, lines in task_sections.items():
            processed_data = process_section(task_type, lines)

                # Generate a unique code and timestamp
            unique_code = str(uuid.uuid4())
            timestamp = datetime.utcnow().isoformat()

            #print("this is something")
            existing_board = await board_collection.find_one({"board_id": int(board)})
           # print(existing_board)
            board_name = existing_board["board_name"]
            
            existing_medium = await medium_collection.find_one({"medium_id": int(medium) })
            #print(existing_medium)
            medium_name = existing_medium["medium_name"]

            existing_grade = await class_collection.find_one({"classs_id": int(grade)})
            #(existing_grade)
            class_name = existing_grade["classs_name"]

            existing_subject = await subject_collection.find_one({"subject_id": int(subject) })
           # print(existing_subject)
            subject_name = existing_subject["subject_name"]

            existing_topic = await topic_collection.find_one({"topic_id": int(lesson) })
           # print(existing_topic)
            topic_name = existing_topic["topic_name"]

            new_filename = f"{board_name[:3]}_{medium_name[:3]}_{class_name}_{subject_name[:3]}_{topic_name}_{task_type}"
            #new_filename = f"{board}{medium}{grade}{subject}{lesson}_{'.'.join(tasks_list)}"
           # print(new_filename)

            # new_filename = f"{board}_{medium}_{grade}_{subject}_{lesson}_{'.'.join(tasks_list)}"
            # new_filename = f"{board_name[:3]}{medium_name[:3]}{grade}{subject_name[:3]}{lesson}_{'.'.join(tasks_list)}"

            #print("Generated filename:", new_filename)

           # print("This is collection2")
            # collection = get_collection(class_name)

            db = await get_or_create_database(board_name)
            print("This is db", db)

            # Get the collection using both the board name and class name
            collection = await get_collection(board_name, class_name)  # Pass both arguments
            print("This is collection", collection)
           # print(collection)

            new_data = {
                "unique_code": unique_code,
                "timestamp": timestamp,
                "board": board,
                "board_name": board_name,
                "medium_name": medium_name,
                "medium": medium,
                "grade": grade,
                "class_name": class_name,
                "subject": subject,
                "subject_name": subject_name,
                "topic_name": topic_name,
                "lesson": lesson
                
            }

            response = await store_task_data(task_type, processed_data,collection,new_filename,new_data)
        if(response['status']=="1"):
            return {
                "message": "File content uploaded successfully",
                "filename": new_filename,
                "status": response['status']  # Send the hasError flag
            }
        else:
            return {
                "message": "Error uploading the file. Please try again.",
                "status": response.get('status')  # Include status in the response on error
            }

    #     form_data = await request.form()
    #     lesson = form_data.get('lesson')  # Fetch lesson from form data dynamically
    #     file_contents = await file.read()
    #     file_extension = file.filename.split('.')[-1].lower()
    #     print(file_extension)

    #     if file_extension == 'pdf':
    #         text = extract_text_from_pdf(file_contents)
    #     elif file_extension in ['doc', 'docx']:
    #         text = extract_text_from_doc(file_contents)
    #         print(text)
    #     else:
    #         raise HTTPException(status_code=400, detail="Unsupported file type")

    #     tasks_list = tasks.split(",")  # Assuming tasks are sent as a comma-separated string
        
    #     # Generate a unique code and timestamp
    #     unique_code = str(uuid.uuid4())
    #     timestamp = datetime.utcnow().isoformat()

    #     print("this is something")
    #     existing_board = await board_collection.find_one({"board_id": int(board)})
    #     print(existing_board)
    #     board_name = existing_board["board_name"]
        
    #     existing_medium = await medium_collection.find_one({"medium_id": int(medium) })
    #     print(existing_medium)
    #     medium_name = existing_medium["medium_name"]

    #     existing_grade = await class_collection.find_one({"classs_id": int(grade)})
    #     print(existing_grade)
    #     class_name = existing_grade["classs_name"]

    #     existing_subject = await subject_collection.find_one({"subject_id": int(subject) })
    #     print(existing_subject)
    #     subject_name = existing_subject["subject_name"]

    #     existing_topic = await topic_collection.find_one({"topic_id": int(lesson) })
    #     print(existing_topic)
    #     topic_name = existing_topic["topic_name"]

    #     new_filename = f"{board_name[:3]}_{medium_name[:3]}_{class_name}_{subject_name[:3]}_{topic_name}_{'.'.join(tasks_list)}"
    #     #new_filename = f"{board}{medium}{grade}{subject}{lesson}_{'.'.join(tasks_list)}"
    #     print(new_filename)

    #     # new_filename = f"{board}_{medium}_{grade}_{subject}_{lesson}_{'.'.join(tasks_list)}"
    #     # new_filename = f"{board_name[:3]}{medium_name[:3]}{grade}{subject_name[:3]}{lesson}_{'.'.join(tasks_list)}"

    #     print("Generated filename:", new_filename)

    #     print("This is collection2")
    #     collection = get_collection(class_name)
    #     print(collection)


    #     # Check for existing files with the same base filename
    #     existing_file = await collection.find_one({"filename": new_filename})

    #     if existing_file:
    #         print("This is existing file")
    #         # print(existing_file)
    #         # Extract existing questions and answers
    #         existing_data = existing_file.get('questions_and_answers', {})

    #         print("this is filename",new_filename)
    #         # Parse new questions and answers
    #         new_data = parse_questions_and_answers(text, new_filename)
            
    #         print("This is new_data")
    #         print(new_data)

            
    #         if new_data:
    #             # if 'question' in new_data:
    #                 # Find the maximum existing question number in the document
    #             max_question_num = max(
    #             [int(key.replace('question', '')) for key in existing_data.keys() if key.startswith('question')] or [0])

    #             # Prepare cleaned data by excluding unnecessary keys like heading and filename
    #             cleaned_new_data = {}
    #             for key, value in new_data.items():
    #                 # if key.startswith('heading') or key == 'filename':
    #                 #     continue  # Skip the heading and filename
    #                 cleaned_new_data[key] = value

    #                 if len(cleaned_new_data) % 2 == 0:
    #                     num_questions = len(cleaned_new_data) // 2
    #                     # print("gljwe    wiyefijb",tasks_list)
    #                     print(f"tasks_list: {tasks_list}")
    #                     if not any(task in tasks_list for task in ['match-the-column', 'multiple-choice-questions', 'true-false']):
    #                         print("'match-the-column' not in tasks_list, proceeding with question and answer processing...")
    #                         for i in range(1, num_questions + 1):
    #                             question_key = f"question{i}"
    #                             answer_key = f"answer{i}"
                                
    #                             new_question_key = f"question{max_question_num + i}"
    #                             new_answer_key = f"answer{max_question_num + i}"
                            
    #                             if question_key in cleaned_new_data and answer_key in cleaned_new_data:
    #                                 existing_data[new_question_key] = cleaned_new_data[question_key]
    #                                 existing_data[new_answer_key] = cleaned_new_data[answer_key]
                                
    #                         # Update the existing document in MongoDB
    #                         results = await collection.update_one(
    #                             {"_id": existing_file["_id"]},
    #                             {"$set": {
    #                                 "questions_and_answers": existing_data,
    #                                 "timestamp": timestamp  # Update the timestamp
    #                             }}
    #                         )
    #                         print(results)
    #                     else:
    #                         print("No questions and answers extracted or incorrect number of keys.")


    #                 if len(cleaned_new_data) % 4 == 0:
    #                     num_questions = len(cleaned_new_data) // 4
                    
    #                     if "multiple-choice-questions" in tasks_list:
    #                         print("Handling multiple-choice questions")
    #                         for i in range(1, num_questions + 1):
    #                             question_key = f"question{i}"
    #                             options_key = f"options{i}"
    #                             answer_key = f"answer{i}"
    #                             explanation_key = f"explanation{i}"
                                
    #                             new_question_key = f"question{max_question_num + i}"
    #                             new_options_key = f"options{max_question_num + i}"
    #                             new_answer_key = f"answer{max_question_num + i}"
    #                             new_explanation_key = f"explanation{max_question_num + i}"
                                
    #                             # Check if all required keys are in the new data
    #                             if question_key in cleaned_new_data:
    #                                 existing_data[new_question_key] = cleaned_new_data[question_key]
    #                             if options_key in cleaned_new_data:
    #                                 existing_data[new_options_key] = cleaned_new_data[options_key]
    #                             if answer_key in cleaned_new_data:
    #                                 existing_data[new_answer_key] = cleaned_new_data[answer_key]
    #                             if explanation_key in cleaned_new_data:
    #                                 existing_data[new_explanation_key] = cleaned_new_data[explanation_key]

    #                         # Update the existing document in MongoDB
    #                         results = await collection.update_one(
    #                             {"_id": existing_file["_id"]},
    #                             {"$set": {
    #                                 "questions_and_answers": existing_data,
    #                                 "timestamp": timestamp  # Update the timestamp
    #                             }}
    #                         )
    #                         print(results)
                        
    #                     elif "true-false" in tasks_list:
    #                         print("Handling true/false questions")
    #                         for i in range(1, num_questions + 1):
    #                             question_key = f"question{i}"
    #                             options_key = f"options{i}"
    #                             answer_key = f"answer{i}"
    #                             explanation_key = f"explanation{i}"
                                
    #                             new_question_key = f"question{max_question_num + i}"
    #                             new_options_key = f"options{max_question_num + i}"
    #                             new_answer_key = f"answer{max_question_num + i}"
    #                             new_explanation_key = f"explanation{max_question_num + i}"
                                
    #                             # Check if all required keys are in the new data
    #                             if question_key in cleaned_new_data:
    #                                 existing_data[new_question_key] = cleaned_new_data[question_key]
    #                             if options_key in cleaned_new_data:
    #                                 existing_data[new_options_key] = cleaned_new_data[options_key]
    #                             if answer_key in cleaned_new_data:
    #                                 existing_data[new_answer_key] = cleaned_new_data[answer_key]
    #                             if explanation_key in cleaned_new_data:
    #                                 existing_data[new_explanation_key] = cleaned_new_data[explanation_key]

    #                         # Update the existing document in MongoDB
    #                         results = await collection.update_one(
    #                             {"_id": existing_file["_id"]},
    #                             {"$set": {
    #                                 "questions_and_answers": existing_data,
    #                                 "timestamp": timestamp  # Update the timestamp
    #                             }}
    #                         )
    #                         print(results)

    #                     elif "match-the-column" in tasks_list:
    #                         print("Handling match-the-column questions")
    #                         for i in range(1, num_questions + 1):
    #                             question_key = f"question{i}"
    #                             column_a_key = f"column_a{i}"
    #                             column_b_key = f"column_b{i}"
    #                             answer_key = f"answer{i}"  # Corrected key name
                                
    #                             # print("KEYY")
                                
    #                             new_question_key = f"question{max_question_num + i}"
    #                             new_column_a_key = f"column_a{max_question_num + i}"
    #                             new_column_b_key = f"column_b{max_question_num + i}"
    #                             new_answer_key = f"answer{max_question_num + i}"  # Corrected key name
                                
    #                             # print("jwkerwkjbe;")

    #                             if question_key in cleaned_new_data and column_a_key in cleaned_new_data and column_b_key in cleaned_new_data and answer_key in cleaned_new_data:
    #                                 existing_data[new_question_key] = cleaned_new_data[question_key]
    #                                 existing_data[new_column_a_key] = cleaned_new_data[column_a_key]
    #                                 existing_data[new_column_b_key] = cleaned_new_data[column_b_key]
    #                                 existing_data[new_answer_key] = cleaned_new_data[answer_key]

    #                         print("This is cleaned new data", cleaned_new_data)

    #                         # Update the existing document in MongoDB
    #                         print("This is existing data", existing_data)
    #                         results = await collection.update_one(
    #                             {"_id": existing_file["_id"]},
    #                             {"$set": {
    #                                 "questions_and_answers": existing_data,
    #                                 "timestamp": timestamp  # Update the timestamp
    #                             }}
    #                         )
    #                         print(results)

    #                     else:
    #                         print("No questions and answers extracted or incorrect number of keys.")
                        
    #     else:
    #         print("hgjhvj;ht;j")
    #         new_data = parse_questions_and_answers(text, new_filename) or {}
    #         # print('hello')
    #         # print('new  data extract',new_data)
    #         if not new_data:
    #             print("No data extracted. Check the extraction logic and data format.")

    #         document = {
    #             "board": board,
    #             "board_name": board_name,
    #             "medium": medium,
    #             "medium_name": medium_name,
    #             "grade": grade,
    #             "grade_name": class_name,
    #             "subject": subject,
    #             "subject_name": subject_name,
    #             "lesson": lesson,
    #             "lesson_name": topic_name,
    #             "filename": new_filename,
    #             "tasks": tasks_list,
    #             "unique_code": unique_code,
    #             "timestamp": timestamp,
    #             "questions_and_answers": new_data
    #         }
    #         result = await collection.insert_one(document)
    #         print("Document to insert:", document)

    #         print("This is detect formatresult collection")
    #         print(result)
    #         return {"file_id": str(result.inserted_id), "message": "File uploaded and saved successfully", "filename": new_filename}

    # return {"message": "File content appended successfully", "filename": new_filename}
            
async def store_task_data(task_type, questions_and_answers,collection,filename,new_data):
    # Create a formatted dictionary for questions and answers
    formatted_questions_and_answers = {}
    for idx, qa in enumerate(questions_and_answers, start=1):
        question_key = f"question{idx}"
        answer_key = f"answer{idx}"
        
        # Handle formatting for different types
        if task_type == 'true-false':
            formatted_questions_and_answers[question_key] = qa['statement']
            formatted_questions_and_answers[answer_key] = qa['answer']
            if 'explanation' in qa:
                explanation_key = f"explanation{idx}"
                formatted_questions_and_answers[explanation_key] = qa['explanation']
        
        elif task_type == 'match-the-column':
            column_a_key = f"column_a{idx}"
            column_b_key = f"column_b{idx}"
            formatted_questions_and_answers[question_key] = "Match the following"
            formatted_questions_and_answers[column_a_key] = qa['column_a']
            formatted_questions_and_answers[column_b_key] = qa['column_b']
            formatted_questions_and_answers[answer_key] = qa['answers']
        
        elif task_type == 'multiple-choice-questions':
            formatted_questions_and_answers[question_key] = qa['question']
            formatted_questions_and_answers[answer_key] = qa['answer']
            if 'options' in qa:
                options_key = f"options{idx}"
                formatted_questions_and_answers[options_key] = qa['options']
            if 'explanation' in qa:
                explanation_key = f"explanation{idx}"
                formatted_questions_and_answers[explanation_key] = qa['explanation']
        
        else:  # For general questions and answers
            formatted_questions_and_answers[question_key] = qa['question']
            formatted_questions_and_answers[answer_key] = qa['answer']

    # Check for existing files with the same base filename
    existing_file = await collection.find_one({"filename": filename})
    if existing_file:
       # If file exists, update the existing document
        result =await collection.update_one(
            {"filename": filename},
            {
                "$set": {"questions_and_answers": formatted_questions_and_answers},
                #"$addToSet": {"tasks": task_type}  # Add task_type to the array if it doesn't already exist
            }
        )
        if result.modified_count > 0:
            print(f"Updated existing file: {filename}")
            return {"status": "1", "message": f"File '{filename}' updated successfully."}
        else:
            print(f"No changes made to the existing file: {filename}")
            return {"status": "0", "message": f"No changes were made to '{filename}'."}

    else:
        # If file doesn't exist, create a new entry with the filename
        document = {
            "board": new_data["board"],
            "board_name": new_data["board_name"],
            "medium": new_data["medium"],
            "medium_name": new_data["medium_name"],
            "grade": new_data["grade"],
            "grade_name": new_data["class_name"],
            "subject": new_data["subject"],
            "subject_name": new_data["subject_name"],
            "lesson": new_data["lesson"],
            "lesson_name": new_data["topic_name"],
            "filename": filename,
            "tasks": [task_type],
            "unique_code": new_data["unique_code"],
            "timestamp": new_data["timestamp"],
            "questions_and_answers": formatted_questions_and_answers
        }
        result = await collection.insert_one(document)
        if result.inserted_id:
            print(f"Inserted new file: {filename}")
            return {"status": "1", "message": f"File '{filename}' inserted successfully."}
        else:
            print(f"Failed to insert the new file: {filename}")
            return {"status": "0", "message": f"Failed to insert '{filename}'."}
    


# Function to preprocess the document by dividing into sections
def preprocess_document(file_content):
    task_sections = {}
    current_task_type = None
    task_content = []
    
    
    for line in file_content.splitlines():
        line = line.strip()
        
        # Identify task headers to define sections
        if re.match(r'Fill in the blanks', line, re.IGNORECASE):
            if current_task_type:
                task_sections[current_task_type] = task_content
            current_task_type = 'fill-in-the-blanks'
            task_content = []
        elif re.match(r'Name the following', line, re.IGNORECASE):
            if current_task_type:
                task_sections[current_task_type] = task_content
            current_task_type = 'name-the-following'
            task_content = []
        elif re.match(r'Answer in one Word', line, re.IGNORECASE):
            if current_task_type:
                task_sections[current_task_type] = task_content
            current_task_type = 'answer-in-one-word'
            task_content = []
        elif re.match(r'Match The Following', line, re.IGNORECASE):
            if current_task_type:
                task_sections[current_task_type] = task_content
            current_task_type = 'match-the-column'
            task_content = []
        elif re.match(r'Multiple Choice Question', line, re.IGNORECASE):
            if current_task_type:
                task_sections[current_task_type] = task_content
            current_task_type = 'multiple-choice-questions'
            task_content = []
        elif re.match(r'True or False', line, re.IGNORECASE):
            if current_task_type:
                task_sections[current_task_type] = task_content
            current_task_type = 'true-false'
            task_content = []
        elif re.match(r'Long Answers', line, re.IGNORECASE):
            if current_task_type:
                task_sections[current_task_type] = task_content
            current_task_type = 'long-answers'
            task_content = []
        elif re.match(r'Short Answers', line, re.IGNORECASE):
            if current_task_type:
                task_sections[current_task_type] = task_content
            current_task_type = 'short-answers'
            task_content = []
        elif re.match(r'Give Reasons', line, re.IGNORECASE):
            if current_task_type:
                task_sections[current_task_type] = task_content
            current_task_type = 'give-reasons'
            task_content = []
        
        # Append line to current task content
        if current_task_type:
            task_content.append(line)
    
    # Add the last section
    if current_task_type:
        task_sections[current_task_type] = task_content
    
    #print("task section found ",task_sections)
    return task_sections

# Function to process each section dynamically
def process_section(task_type, lines):
    processed_data = []
    
    if task_type == 'fill-in-the-blanks' or task_type == 'answer-in-one-word' or task_type == 'give-reasons' or task_type == 'name-the-following':
        
        for i, line in enumerate(lines):
            
           # Find the position of 'Answer:'
          
            # Find the position of the question, ignoring the numbering
            question_match = re.match(r'^\d+\.\s*(.*)', line)
            if question_match:
                question = question_match.group(1).strip()  # Extract the question part

                # Check if the next line is the answer
                if i + 1 < len(lines) and lines[i + 1].startswith("Answer:"):
                    answer = lines[i + 1][len("Answer:"):].strip()  # Extract the answer
                    
                    # Append to processed_data only if both question and answer are found
                    processed_data.append({
                        "question": question,
                        "answer": answer
                    })

            

    elif task_type == 'match-the-column':
        match_pairs = []
        column_a = []
        column_b = []
        answers = []
        question = []

       # pattern = r'^\d+\.\s*(.*)\s*-\s*[A-Z]\.\s*(.*)$'  # Format: "1. Item - A. Match"
        # Split the input text into lines
       # lines = txts.strip().splitlines()

        # Variable to track the current section
        current_section = None

        for line in lines:
            line = line.strip()  # Remove leading and trailing whitespace
            
            # Check if we are in a new "Column A" section (indicating a new question set)
            if line.startswith("Column A"):
                # Save the previous set of data before starting a new set
                if column_a or column_b or answers:
                    processed_data.append({
                        "column_a": column_a,
                        "column_b": column_b,
                        "answers": answers
                    })
                    # Reset for the new block
                    column_a = []
                    column_b = []
                    answers = []
                current_section = 'column_a'
                continue  # Skip to the next line
            
            # Check if we are in "Column B"
            elif line.startswith("Column B"):
                current_section = 'column_b'
                continue
            
            # Check if we are in the "Answer" section
            elif line.startswith("Answer"):
                current_section = 'answers'
                continue
            
            # Based on the current section, store the lines
            if current_section == 'column_a' and line:
                column_a.append(line)
            elif current_section == 'column_b' and line:
                column_b.append(line)
            elif current_section == 'answers' and line:
                answers.append(line)

        # After the loop, save the last set of data
        if column_a or column_b or answers:
            processed_data.append({
                "column_a": column_a,
                "column_b": column_b,
                "answers": answers
            })

       

    elif task_type == 'multiple-choice-questions':
        current_question = {}
        for line in lines:
            if re.match(r'^\d+\.\s*(.*)$', line):  # Question Line
                if current_question:
                    processed_data.append(current_question)
                current_question = {"question": line.strip(), "options": [], "answer": ""}
            elif re.match(r'^[A-D]\)\s*(.*)$', line):  # Option Line
                option_match = re.match(r'^[A-D]\)\s*(.*)$', line)
                current_question["options"].append(option_match.group(1).strip())
            elif re.match(r'^Answer:\s*(.*)$', line):  # Answer Line
                answer_match = re.match(r'^Answer:\s*(.*)$', line)
                current_question["answer"] = answer_match.group(1).strip()
            elif re.match(r'^Explanation:\s*(.*)$', line):  # Answer Line
                explanation_match = re.match(r'^Explanation:\s*(.*)$', line)
                current_question["explanation"] = explanation_match.group(1).strip()
        
        if current_question:
            processed_data.append(current_question)

    elif task_type == 'true-false':
        current_statement = ""
        current_answer = ""
        current_explanation = ""

        for i, line in enumerate(lines):
            # Match the statement followed by choices
            statement_match = re.match(r'^\d+\.\s*(.*)', line)
            
            if statement_match:
                if current_statement and current_answer and current_explanation:
                    processed_data.append({
                        "statement": current_statement.strip(),
                        "answer": current_answer.strip(),
                        "explanation": current_explanation.strip()
                    })
                
                current_statement = statement_match.group(1).strip()  # Start new statement
                current_answer = ""
                current_explanation = ""

            elif line.startswith("Answer:"):
                current_answer = line[len("Answer:"):].strip()  # Extract the answer
            
            elif line.startswith("Explanation:"):
                current_explanation = line[len("Explanation:"):].strip()  # Extract the explanation
            
            # Append the last statement after loop ends
        if current_statement and current_answer and current_explanation:
            processed_data.append({
                "statement": current_statement.strip(),
                "answer": current_answer.strip(),
                "explanation": current_explanation.strip()
            })

    elif task_type == 'long-answers' or task_type == 'short-answers':
        current_question = ""  # Track the current question
        current_answer = ""  # Track the current answer
        for i, line in enumerate(lines):
            # Match questions based on numbered format
            question_match = re.match(r'^\d+\.\s*(.*)', line)
            
            if question_match:
                # If there was a previous question, save it with its answer
                if current_question and current_answer:
                    processed_data.append({
                        "question": current_question.strip(),
                        "answer": current_answer.strip()
                    })
                
                # Start a new question
                current_question = question_match.group(1).strip()
                current_answer = ""  # Reset the current answer for the new question
            
            elif line.startswith("Answer:"):
                # Append the answer, as it may be long or multiline
                current_answer += line[len("Answer:"):].strip()

        # Append the final question-answer pair after looping
        if current_question and current_answer:
            processed_data.append({
                "question": current_question.strip(),
                "answer": current_answer.strip()
            })

   # print("processd data",processed_data)
    return processed_data 

def extract_text_from_pdf(file_contents: bytes) -> str:
    text = ""
    with fitz.open(stream=file_contents, filetype="pdf") as pdf_document:
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text += page.get_text()
    return text

def extract_text_from_doc(file_contents: bytes) -> str:
    text = ""
    doc = Document(io.BytesIO(file_contents))
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

def detect_format(line, next_line):
    """Detect the format of the question based on the line content."""
    line = line.strip()
    next_line = next_line.strip()
    
    if re.match(r'^\d+\.', line):
        if next_line.startswith("Answer:"):
            print("Format found: question and answer")
            return 'question_answer'
        # if re.match(r'^[A-Da-d]\.', next_line) or re.match(r'^[1-4]\.', next_line):
        #     print("Format found: mcq")
        #     return 'mcq'

        # for Mcq
        if re.match(r'^\d+\.', line):
        # Check if the next line starts with an option (A), (B), (C), (D)
            if re.match(r'^[A-D]\)', next_line):
                print("Format found: mcq")
                return 'mcq'
            elif next_line.startswith("Answer:"):
                print("Format found: question_answer with answer line")
                return 'mcq'
            elif next_line.startswith("Explanation:"):
                print("Format found: expanation ")
                return 'mcq'
            
            #  For trueorFalse      
            if re.match(r'^\d+\.', line):
            # Check if the next line starts with an option (A), (B)
                if re.match(r'^[A-B]\)', next_line):
                    print("Format found: trueorfalse")
                    return 'trueorfalse'
                elif next_line.startswith("Answer:"):
                    print("Format found: question_answer with answer line")
                    return 'trueorfalse'
                elif next_line.startswith("Explanation:"):
                    print("Format found: explanation ")
                    return 'trueorfalse'
            
            # Detecting the format based on presence of columns and answers
            if re.match(r'^[1-5]\.', line) :
                print("Format found: matchthecolumn ")
                return 'matchthecolumn'
            elif re.match(r'^[A-E]\.', line):
                print("Format found: matchthecolumn")
                return 'matchthecolumn'
            elif line.startswith("Answers"):
                print("Format found: matchthecolumn")
                return 'matchthecolumn'
            
        return None


def extract_question_and_answer(lines, line_index):
    """Extract question and answer."""
    line = lines[line_index].strip()
    question = line[len(re.match(r'^\d+\.', line).group()):].strip()
    answer_line_index = line_index + 1
    if answer_line_index < len(lines) and lines[answer_line_index].startswith("Answer:"):
        answer = lines[answer_line_index][len("Answer:"):].strip()
        return question, answer
    return None, None

def extract_mcq_details(lines, index):
    """Extract question, options, answer, and explanation for MCQ format."""
    question = lines[index].strip()
    options = []
    answer = None
    explanation = None

    # Loop through the following lines to find options, answer, and explanation
    for i in range(index + 1, len(lines)):
        line = lines[i].strip()
        
        # Match options (A) option text
        if re.match(r'^[A-D]\)', line):
            options.append(line)
        
        # Match answer line
        elif line.startswith("Answer:"):
            answer = line
        
        # Match explanation line
        elif line.startswith("Explanation:"):
            explanation = line
            break  # Assuming explanation is the last piece of information

    if question and options and answer:
        return {
            'question': question,
            'options': options,
            'answer': answer,
            'explanation': explanation
        }
    return None

def extract_trueorfalse_details(lines, index):
    """Extract question, options, answer, and explanation for MCQ format."""
    question = lines[index].strip()
    options = []
    answer = None
    explanation = None

    # Loop through the following lines to find options, answer, and explanation
    for i in range(index + 1, len(lines)):
        line = lines[i].strip()
        
        # Match options (A) option text
        if re.match(r'^[A-B]\)', line):
            options.append(line)
        
        # Match answer line
        elif line.startswith("Answer:"):
            answer = line
        
        # Match explanation line
        elif line.startswith("Explanation:"):
            explanation = line
            break  # Assuming explanation is the last piece of information

    if question and options and answer:
        return {
            'question': question,
            'options': options,
            'answer': answer,
            'explanation': explanation
        }
    return None


def extract_matchthecolumn_details(txts):
    # print("Lines")
    # print(lines)
    """Extracts details from the 'Match the Following' question format."""
    
    column_a = []
    column_b = []
    answers = []
    question = []


    # Split the input into sections based on the headers
    sections = txts.strip().split("\n\n")
    
    # Store the sections directly into the desired arrays
    question = sections[0].strip()
    column_a = sections[1].splitlines()[1:]  # Exclude the header "Column A"
    column_b = sections[2].splitlines()[1:]  # Exclude the header "Column B"
    answers = sections[3].splitlines()[1:]    # Exclude the header "Answer"

    # # Display the results
    # print("Column A:", column_a)
    # print("Column B:", column_b)
    # print("Answers:", answers)

    return {
        'question': question,
       'column_a': column_a,
       'column_b': column_b,
       'answers': answers
     }
   


def parse_questions_and_answers(text: str, filename: str):
    lines = text.strip().split('\n')
    data = {}
    heading_set = False
    question_counter = 1

    for i in range(len(lines)):
        line = lines[i].strip()

        # Detect heading (only set once)
        if not heading_set and line.startswith("Chapter:"):
            data["heading"] = line
            heading_set = True
            continue

        # Check next line for format detection
        next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""

        # Detect format
        format_detected = detect_format(line, next_line)
        # print(f"Detected format for line '{line}': {format_detected}")

        if format_detected == 'question_answer':
            print("This is question&answers")
            question, answer = extract_question_and_answer(lines, i)
            if question and answer:
                data[f"question{question_counter}"] = question
                data[f"answer{question_counter}"] = answer
                question_counter += 1
            else:
                print(f"Failed to extract question or answer for line: {line}")

        elif format_detected == 'mcq' :
            print("This is mcq format")
            mcq_data = extract_mcq_details(lines, i)
            print("This is mcq_data")
            print(mcq_data)
            if mcq_data:
                print("This is in if condition")
                data[f"question{question_counter}"] = mcq_data['question']
                data[f"options{question_counter}"] = mcq_data['options']
                data[f"answer{question_counter}"] = mcq_data['answer']
                data[f"explanation{question_counter}"] = mcq_data.get('explanation', '')
                question_counter += 1
            else:
                print(f"Failed to extract question,option and answer for line: {line}")
        
        elif format_detected == 'trueorfalse' :
            print("This is trueorfasle format")
            trueorfalse = extract_trueorfalse_details(lines, i)
            if trueorfalse:
                print("This is in if condition")
                data[f"question{question_counter}"] = trueorfalse['question']
                data[f"options{question_counter}"] =trueorfalse['options']
                data[f"answer{question_counter}"] = trueorfalse['answer']
                data[f"explanation{question_counter}"] = trueorfalse.get('explanation', '')
                question_counter += 1
            else:
                print(f"Failed to extract question,option and answer for line: {line}")

        # elif format_detected == 'matchthecolumn':
        #     # print("hghkjhjhjkh",extract_matchthecolumn_details)
        #     matchthefollowing = extract_matchthecolumn_details(text)
        #     print("This is match the column",matchthefollowing)
        #     if matchthefollowing:
        #         print("This is in if condition")
        #         # Ensure the data is correctly formatted for storage
        #         data[f"column_a{question_counter}"] = matchthefollowing['column_a']
        #         data[f"column_b{question_counter}"] = matchthefollowing['column_b']
        #         data[f"answer{question_counter}"] = matchthefollowing['answers']
        #         question_counter += 1
        #     else:
        #         print(f"Failed to extract column data for format: {format_detected}")

    if format_detected == 'matchthecolumn':
            # print("hghkjhjhjkh",extract_matchthecolumn_details)
            matchthefollowing = extract_matchthecolumn_details(text)
            print("This is match the column",matchthefollowing)
            if matchthefollowing:
                print("This is in if condition")
                # Ensure the data is correctly formatted for storage
                data[f"question{question_counter}"] = matchthefollowing['question']
                data[f"column_a{question_counter}"] = matchthefollowing['column_a']
                data[f"column_b{question_counter}"] = matchthefollowing['column_b']
                data[f"answer{question_counter}"] = matchthefollowing['answers']
                question_counter += 1
            else:
                print(f"Failed to extract column data for format: {format_detected}")

    # Print data to verify its structure
    print("Data to be stored in database:", data)

    # Add filename to the data
    # data["filename"] = filename
    return data

@app.get("/retrieve", response_class=HTMLResponse)
async def get_retrieve_page():
    print("This is retrieve")
    with open("static/example_screen.html") as f:
        # return f.read()
        return HTMLResponse(content=f.read(), status_code=200)


@app.get("/getsubjects")
async def get_subjects(
    board: str = Query(...),
    medium: str = Query(...),
    grade: str = Query(...)
):
    # Build query
    query = {
        "board_id": board,
        "medium_id": medium,
        "class_id": grade
    }

    print("This is 1st query")
    print(query)

    # Access collection
    collection = get_collection(grade)
    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Fetch subjects
    subjects = await collection.distinct("subject", query)
    print(subjects)
    return {"subjects": subjects}

@app.get("/getchaptersandtasks")
async def get_chapters_and_tasks(
    board: str = Query(...),
    medium: str = Query(...),
    grade: str = Query(...),
    subject: str = Query(...)
):
    existing_grade = await class_collection.find_one({"classs_id": int(grade)})
    print(existing_grade)
    class_name = existing_grade["classs_name"]

    # Construct the query, keep the fields as strings if they are stored as strings
    query = {
        "board_id": int(board),
        "medium_id": int(medium),
        "class_id": int(grade),
        "subject_id": int(subject)
    }

    # Debugging the query
    print("This is the query being executed:")
    print(query)

    # Get the MongoDB collection
    collection = get_collection(class_name)
    print("Acha collection hai")
    print(collection)
    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Execute the MongoDB queries
    chapters = await topic_collection.distinct("topic_name", query)
    tasks = await collection.distinct("tasks", query)
    print("Chapters:", chapters)
    print("Tasks:", tasks)
    
    return {"chapters": chapters, "tasks": tasks}


@app.get("/get_questions_and_answers")
async def get_questions_and_answers(
    board: str = Query(...),
    medium: str = Query(...),
    grade: str = Query(...),
    subject: str = Query(...),
    lesson: str = Query(...),
    tasks: str = Query(...),
    limit: Optional[int] = Query(None, ge=1)  # Ensure limit is >= 1
):
    
    # Validate limit
    if limit is not None and limit < 1:
        raise HTTPException(status_code=422, detail="Limit must be at least 1")

    existing_board = await board_collection.find_one({"board_id": int(board)})
    print(existing_board)
    board_name = existing_board["board_name"]

    existing_grade = await class_collection.find_one({"classs_id": int(grade)})
    print(existing_grade)
    class_name = existing_grade["classs_name"]

    # Construct the query
    query = {
        "board": board,
        "medium":medium,
        "grade": grade,
        "subject":subject,
        "lesson": lesson,
        "tasks": {"$in": tasks.split(",")}
    }

    print("Query:", query)
    
    # # Get the collection based on grade
    # collection = get_collection(class_name)
    db = await get_or_create_database(board_name)
    print("This is db", db)

    # Get the collection using both the board name and class name
    collection = await get_collection(board_name, class_name)  # Pass both arguments
    print("This is collection", collection)
    
    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Find the document based on the query
    document = await collection.find_one(query)
    if not document:
        print("No document found for query")
        raise HTTPException(status_code=404, detail="No data found for the specified criteria")

    # Extract the question numbers
    questions_and_answers = document.get("questions_and_answers", {})
    question_numbers = [
        int(key.replace('question', '')) for key in questions_and_answers.keys()
        if key.startswith('question') and key.replace('question', '').isdigit()
    ]

    question_numbers.sort()

    # Apply random sampling if a limit is specified
    if limit > len(question_numbers):
        limit = len(question_numbers)
    selected_question_numbers = random.sample(question_numbers, limit)

    # Prepare the result
    result = []

    if not any(task in tasks for task in ['match-the-column', 'multiple-choice-questions', 'true-false']):
        for number in selected_question_numbers:
            question_key = f"question{number}"
            answer_key = f"answer{number}"
            result.append({
                "question": questions_and_answers.get(question_key, ""),
                "answer": questions_and_answers.get(answer_key, "")
            })

        print('final result',result)

    elif any(task in tasks for task in ['multiple-choice-questions', 'true-false']): 
        for number in selected_question_numbers:
            question_key = f"question{number}"
            options_key = f"options{number}"
            answer_key = f"answer{number}"
            explanation_key = f"explanation{number}"

            result.append({
                "question": questions_and_answers.get(question_key, ""),
                "options": questions_and_answers.get(options_key, ""),
                "answer": questions_and_answers.get(answer_key, ""),
                "explanation": questions_and_answers.get(explanation_key, "")
            })

        print('final result',result)

    elif any(task in tasks for task in ['match-the-column']): 
        for number in selected_question_numbers:
            question_key = f"question{number}"
            column_a_key = f"column_a{number}"
            column_b_key = f"column_b{number}"
            answer_key = f"answer{number}"

            result.append({
                "question": questions_and_answers.get(question_key, ""),
                "column_a": questions_and_answers.get(column_a_key, ""),
                "column_b": questions_and_answers.get(column_b_key, ""),
                "answer": questions_and_answers.get(answer_key, "")
            })

        print('final result',result)

    return {"questions_and_answers": result}

@app.get("/get_textbook-solution")
async def get_questions_and_answers(
    board: str = Query(...),
    medium: str = Query(...),
    grade: str = Query(...),
    subject: str = Query(...),
    lesson: str = Query(...),
    tasks: str = Query(...),
   
):

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

    existing_board = await board_collection.find_one({"board_id": int(board)})
    print(existing_board)
    board_name = existing_board["board_name"]

    existing_grade = await class_collection.find_one({"classs_id": int(grade)})
    print(existing_grade)
    class_name = existing_grade["classs_name"]

    # collection = get_collection(class_name)
   # print(collection)
    # Get the collection based on grade

    db = await get_or_create_database(board_name)
    print("This is db", db)

    # Get the collection using both the board name and class name
    collection = await get_collection(board_name, class_name)  # Pass both arguments
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
       
      
    return {"document": document}

@app.get("/get_SamplePaper-solution")
async def get_questions_and_answers(
    board: str = Query(...),
    medium: str = Query(...),
    grade: str = Query(...),
    subject: str = Query(...),
    tasks: str = Query(...),
   
):

    # Construct the query
    query = {
        "board": board,
        "medium": medium,
        "grade": grade,
        "subject": subject,
        
        "tasks": tasks
    }

   

    print("Query:", query)

    existing_board = await board_collection.find_one({"board_id": int(board)})
    print(existing_board)
    board_name = existing_board["board_name"]

    existing_grade = await class_collection.find_one({"classs_id": int(grade)})
    print(existing_grade)
    class_name = existing_grade["classs_name"]

    # collection = get_collection(class_name)
   # print(collection)
    # Get the collection based on grade

    db = await get_or_create_database(board_name)
    print("This is db", db)

    # Get the collection using both the board name and class name
    collection = await get_collection(board_name, class_name)  # Pass both arguments
    print("This is collection", collection)
   
    if collection is None:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Find the document based on the query
   # document = await collection.find(query)
    documents = await collection.find(query).to_list(length=None)  # Convert cursor to list
    if not documents:
    
        print("No document found for query")
        raise HTTPException(status_code=404, detail="No data found for the specified criteria")
    else:
         # Convert ObjectId to string for JSON serialization
        for doc in documents:
            doc['_id'] = str(doc['_id'])

       # document['_id'] = str(document['_id'])
       
      
    return {"document": documents}

# Login part start here

# Initialize CryptContext for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(BaseModel):
    role: str
    name: str
    surname: str
    institute_name: str
    class_name: str
    unique_institute_id: str
    date_of_birth: str
    email: str
    password: str

class Board(BaseModel):
    boardName: str
   

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

# @app.get("static/register.html", response_class=HTMLResponse)
# async def get_form():
#     with open("static/register.html", 'rb') as f:
#         content = f.read()s
#         return content.decode('utf-8')
    
async def register_user(user: User):
    hashed_password = pwd_context.hash(user.password)
    print("this is new user",user)
    # Assign role_id based on the role
    role_id = get_role_id(user.role)
    print(role_id)
    
    # Create user profile data
    user_profile = {
        "role": user.role,
        "name": user.name,
        "surname": user.surname,
        "institute_name": user.institute_name,
        "class_name": user.class_name,
        "unique_institute_id": user.unique_institute_id,
        "date_of_birth": user.date_of_birth,
        "email": user.email
    }

    # Create auth data
    auth_data = {
        "role": user.role,
        "email": user.email,
        "password": hashed_password,
        "role_id": role_id,  # Store the role_id
        "unique_institute_id": user.unique_institute_id
    }

    existing_user = await profiles_collection.find_one({"role": user.role,
                                                        "email": user.email,
                                                        "class_name":user.class_name,
                                                        "unique_institute_id": user.unique_institute_id,
                                                        "date_of_birth": user.date_of_birth
                                                        })
    print(existing_user)

    # Check if the email is already registered
    # if auth_collection.find_one({"email": user.email}):
    if existing_user:
        raise HTTPException(status_code=400, detail="User is already registered")
    else:
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
    unique_institute_id: str

@app.post("/student-teacher-login")
async def student_teacher_login(data: StudentTeacherLoginData):
    user_auth = await auth_collection.find_one({
        "email": data.email,
        "role_id": data.role_id,
        "unique_institute_id": data.unique_institute_id
    })

    # Check if user exists
    if not user_auth:
        raise HTTPException(status_code=404, detail="User not found. Please check your email, institute ID, or role.")

    if not pwd_context.verify(data.password, user_auth['password']):
        raise HTTPException(status_code=401, detail="Incorrect password")

    return {"message": "Login successful"}
    
@app.post("/admin-login")
async def admin_login(data: LoginData):
    # Query to find user in auth collection by email and role_id
    user_auth = await auth_collection.find_one({"email": data.email, "role_id": data.role_id})

    if user_auth:
            # Verify the entered password against the stored hashed password
            if pwd_context.verify(data.password, user_auth['password']):
                return {"message": "Login successful"}
            else:
                raise HTTPException(status_code=401, detail="Incorrect password")
    else:
            return {"message": "User not found. Please register first."}
    
@app.post("/add_board")
async def board_added(board: Board):
    print(board.boardName)
    # Check if the email is already registered
    existing_board = await board_collection.find_one({"board_name": board.boardName})
    if existing_board:
        return {"message": "Board already registered"}
    # if board_collection.find_one({"board_name": board.boardName}):
      
    #     raise HTTPException(status_code=400, detail="Board already registered")
    
    last_record = await board_collection.find_one(sort=[("board_id", DESCENDING)])

    print(last_record)
    # If no records exist, start with ID 1
    if last_record:
        new_id = last_record["board_id"] + 1
    else:
        new_id = 1

    # Create user profile data
    board_profile = {
        "board_name": board.boardName,
        "board_id":new_id
    }
    print("main yaha hoon yaha hoon yaha hoon yaha")
    print(board_profile)
    # Insert data into both collections
    board_collection.insert_one(board_profile)
 
    return {"message": "Board added successful"}

@app.get("/get_SchoolBoard")
async def get_boards(request: Request):  # Accepting the Request object
    # print("virus mila hai")
    try:
        cursor = board_collection.find()
        boards = await cursor.to_list(length=None)

        # Convert ObjectId to string
        for board in boards:
            board['_id'] = str(board['_id'])

        return boards
    except Exception as e:
        print(f"Unhandled Exception: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

class Update_Board(BaseModel):
    board_id: int
    board_name: str  

@app.put("/update_board")
async def update_board(board: Update_Board):
    print("this is board", board)

    # Find the board by ID
    existing_board = await board_collection.find_one({"board_id": board.board_id})

    if not existing_board:
        raise HTTPException(status_code=404, detail="Board not found")

    # Update the board name
    result = await board_collection.update_one(
        {"board_id": board.board_id},
        {"$set": {"board_name": board.board_name}}  # Corrected to use board.board_name
    )

    if result.modified_count == 1:
        return {"message": "Board updated successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to update medium")

    
@app.delete("/delete_board/{board_id}")
async def delete_board(board_id: int):
    try:
        # Check if the board exists
        existing_board = await board_collection.find_one({"board_id": board_id})
        if not existing_board:
            raise HTTPException(status_code=404, detail="Board not found")

        # Perform the delete operation
        await board_collection.delete_one({"board_id": board_id})

        return {"message": "Board deleted successfully"}
    except Exception as e:
        print(f"Unhandled Exception: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

class Medium(BaseModel):
    mediumName: str    

@app.post("/add_medium")
async def medium_added(medium: Medium):
    # print(board.boardName)
    # Check if the email is already registered
    existing_medium = await board_collection.find_one({"medium_name": medium.mediumName})
    if existing_medium:
        return {"message": "Medium already registered"}
    # if board_collection.find_one({"board_name": board.boardName}):
      
    #     raise HTTPException(status_code=400, detail="Board already registered")
    
    last_record = await medium_collection.find_one(sort=[("medium_id", DESCENDING)])

    # print(last_record)
    # If no records exist, start with ID 1
    if last_record:
        new_id = last_record["medium_id"] + 1
    else:
        new_id = 1

    # Create user profile data
    medium_profile = {
        "medium_name": medium.mediumName,
        "medium_id":new_id
    }
    
    medium_collection.insert_one(medium_profile)
 
    return {"message": "Medium added successful"}

@app.get("/get_SchoolMedium")
async def get_mediums(request: Request):  # Accepting the Request object
    try:
        cursor = medium_collection.find()
        mediums = await cursor.to_list(length=None)

        # Convert ObjectId to string
        for medium in mediums:
            medium['_id'] = str(medium['_id'])

        return mediums
    except Exception as e:
        print(f"Unhandled Exception: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")
    
class Update_Medium(BaseModel):
    medium_id: int
    medium_name: str  

@app.put("/update_medium")
async def update_medium(medium: Update_Medium):
    print("this is medium", medium)

    # Find the medium by ID
    existing_medium = await medium_collection.find_one({"medium_id": medium.medium_id})

    if not existing_medium:
        raise HTTPException(status_code=404, detail="Medium not found")

    # Update the medium name
    result = await medium_collection.update_one(
        {"medium_id": medium.medium_id},  # Corrected field
        {"$set": {"medium_name": medium.medium_name}}  # Correct field for update
    )

    if result.modified_count == 1:
        return {"message": "Medium updated successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to update medium")

@app.delete("/delete_medium/{medium_id}")
async def delete_medium(medium_id: int):
    try:
        # Check if the medium exists
        existing_medium = await medium_collection.find_one({"medium_id": medium_id})
        if not existing_medium:
            raise HTTPException(status_code=404, detail="Medium not found")

        # Perform the delete operation
        await medium_collection.delete_one({"medium_id": medium_id})

        return {"message": "Medium deleted successfully"}
    except Exception as e:
        print(f"Unhandled Exception: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


class Institute(BaseModel):
    instituteName: str    

@app.post("/add_institute")
async def institute_added(institute: Institute):
   
    existing_institute = await institute_collection.find_one({"institute_name": institute.instituteName})
    if existing_institute:
        return {"message": "Medium already registered"}
    
    last_record = await institute_collection.find_one(sort=[("institute_id", DESCENDING)])

    if last_record:
        new_id = last_record["institute_id"] + 1
    else:
        new_id = 1

    # Create user profile data
    institute_profile = {
        "institute_name": institute.instituteName,
        "institute_id":new_id
    }
   
    institute_collection.insert_one(institute_profile)
 
    return {"message": "Institute added successful"}

@app.get("/get_SchoolInstitute")
async def get_institutes(request: Request):  # Accepting the Request object
    try:
        cursor = institute_collection.find()
        institutes = await cursor.to_list(length=None)

        # Convert ObjectId to string
        for institute in institutes:
            institute['_id'] = str(institute['_id'])

        return institutes
    except Exception as e:
        print(f"Unhandled Exception: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")
    
class Update_Institute(BaseModel):
    institute_id: int
    institute_name: str  

@app.put("/update_institute")
async def update_institute(institute: Update_Institute):
    print("this is institute", institute)

    # Find the institute by ID
    existing_institute = await institute_collection.find_one({"institute_id": institute.institute_id})

    if not existing_institute:
        raise HTTPException(status_code=404, detail="Institute not found")

    # Update the medium name
    result = await institute_collection.update_one(
        {"institute_id": institute.institute_id},  # Corrected field
        {"$set": {"institute_name": institute.institute_name}}  # Correct field for update
    )

    if result.modified_count == 1:
        return {"message": "Institute updated successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to update institute")


@app.delete("/delete_institute/{institute_id}")
async def delete_institute(institute_id: int):
    try:
        # Check if the institute exists
        existing_institute = await institute_collection.find_one({"institute_id": institute_id})
        if not existing_institute:
            raise HTTPException(status_code=404, detail="Institute not found")

        # Perform the delete operation
        await institute_collection.delete_one({"institute_id": institute_id})

        return {"message": "Institute deleted successfully"}
    except Exception as e:
        print(f"Unhandled Exception: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
    
class Class(BaseModel):
    className: str    

@app.post("/add_class")
async def class_added(classs: Class):
    existing_class = await class_collection.find_one({"classs_name": classs.className})
    if existing_class:
        return {"message": "Class already registered"}
    
    last_record = await class_collection.find_one(sort=[("classs_id", DESCENDING)])

    if last_record:
        new_id = last_record["classs_id"] + 1
    else:
        new_id = 1

    # Create class profile data
    class_profile = {
        "classs_name": classs.className,
        "classs_id": new_id
    }
   
    await class_collection.insert_one(class_profile)
 
    return {"message": "Class added successfully"}

@app.get("/get_SchoolClass")
async def get_classs(request: Request):  
    try:
        cursor = class_collection.find()
        classs = await cursor.to_list(length=None)

        # Convert ObjectId to string
        for cls in classs:
            cls['_id'] = str(cls['_id'])  # If you need to convert _id, otherwise remove this

        return classs  # Return the list of classes
    except Exception as e:
        print(f"Unhandled Exception: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")
    
class Update_Class(BaseModel):
    classs_id: int
    classs_name: str  

@app.put("/update_class")
async def update_class(classs: Update_Class):
    print("this is classs", classs)

    # Find the institute by ID
    existing_class = await class_collection.find_one({"classs_id": classs.classs_id})

    if not existing_class:
        raise HTTPException(status_code=404, detail="Class not found")

    # Update the medium name
    result = await class_collection.update_one(
        {"classs_id": classs.classs_id},  # Corrected field
        {"$set": {"classs_name": classs.classs_name}}  # Correct field for update
    )

    if result.modified_count == 1:
        return {"message": "Class updated successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to update Class")

@app.delete("/delete_class/{classs_id}")
async def delete_class(classs_id: int):
    try:
        # Check if the class exists
        existing_class = await class_collection.find_one({"classs_id": classs_id})
        if not existing_class:
            raise HTTPException(status_code=404, detail="Class not found")

        # Perform the delete operation
        await class_collection.delete_one({"classs_id": classs_id})

        return {"message": "Class deleted successfully"}
    except Exception as e:
        print(f"Unhandled Exception: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

# For subject Part Shazzi ma'am
class Subject(BaseModel):
    subjectName: str
    className: str
    mediumName: str
    boardName: str

@app.post("/add_subject")
async def subject_added(subjt: Subject):
    
    # Check if the email is already registered
    existing_subject = await subject_collection.find_one({"subject_name": subjt.subjectName, "class_id":subjt.className, "medium_id":subjt.mediumName, "board_id":subjt.boardName })
    if existing_subject:
        return {"message": "Subject already registered"}
        
    last_record = await subject_collection.find_one(sort=[("subject_id", DESCENDING)])

    #print(last_record)
    # If no records exist, start with ID 1
    if last_record:
        new_id = last_record["subject_id"] + 1
    else:
        new_id = 1

    # Create user profile data
    subject_profile = {
        "subject_name": subjt.subjectName,
        "subject_id":new_id,
        "class_id":subjt.className,
        "medium_id":subjt.mediumName,
        "board_id":subjt.boardName

    }
    print("main yaha hoon yaha hoon yaha hoon yaha")
    print(subject_profile)
    # Insert data into both collections
    subject_collection.insert_one(subject_profile)
 
    return {"message": "Subject added successful"}

class SubjectDtl(BaseModel):
    className: str
    mediumName: str
    boardName: str


@app.post("/get_SubjectDetails")
async def subject_details(subjt: SubjectDtl):
    print(subjt)
    try:
        # Fetch the subjects from MongoDB
        subjects = await subject_collection.find({
            "class_id": subjt.className,
            "medium_id": subjt.mediumName,
            "board_id": subjt.boardName
        }).to_list(length=None)

        # Convert ObjectId to string
        for subject in subjects:
            if "_id" in subject:
                subject["_id"] = str(subject["_id"])  # Convert ObjectId to string

        return subjects

    except Exception as e:
        print(f"Unhandled Exception: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.get("/get_SubjectDetails1")
async def get_subject_details(request: Request):
    try:
        # Fetch all subjects
        cursor = subject_collection.find()
        subjects = await cursor.to_list(length=None)

        # Create a list to store detailed subject information
        detailed_subjects = []

        # Iterate through subjects and fetch related class, medium, and board details
        for subject in subjects:
            subject["_id"] = str(subject["_id"])  # Convert ObjectId to string

            # Fetch the subject_id directly
            subject_id = subject.get("subject_id", "Unknown subject_ID")
            # Convert class_id, medium_id, and board_id to int for the query

            try:
                class_id = int(subject.get("class_id", 0))
                medium_id = int(subject.get("medium_id", 0))
                board_id = int(subject.get("board_id", 0))
            except ValueError:
                print(f"Invalid ID format for subject {subject['_id']}")
                class_id, medium_id, board_id = None, None, None

            print(f"Subject ID: {subject['_id']}")
            print(f"Class ID: {class_id} (Type: {type(class_id)})")
            print(f"Medium ID: {medium_id} (Type: {type(medium_id)})")
            print(f"Board ID: {board_id} (Type: {type(board_id)})")

            # Fetch class name based on class_id
            class_data = await class_collection.find_one({"classs_id": class_id})
            subject["class_name"] = class_data["classs_name"] if class_data else "Unknown Class"
            if not class_data:
                print(f"No class found for class_id: {class_id}")

            # Fetch medium name based on medium_id
            medium_data = await medium_collection.find_one({"medium_id": medium_id})
            subject["medium_name"] = medium_data["medium_name"] if medium_data else "Unknown Medium"
            if not medium_data:
                print(f"No medium found for medium_id: {medium_id}")

            # Fetch board name based on board_id
            board_data = await board_collection.find_one({"board_id": board_id})
            subject["board_name"] = board_data["board_name"] if board_data else "Unknown Board"
            if not board_data:
                print(f"No board found for board_id: {board_id}")

            # Append the subject with the fetched details
            detailed_subjects.append({
                "_id": subject["_id"],
                "subject_id": subject_id,  # Add subject_id here
                "subject_name": subject["subject_name"],
                "class_name": subject["class_name"],
                "medium_name": subject["medium_name"],
                "board_name": subject["board_name"]
            })

        return detailed_subjects
    
    except Exception as e:
        print(f"Unhandled Exception: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")
    
class Update_Subject(BaseModel):
    subject_id: int
    subject_name: str


@app.put("/update_subject")
async def update_subject(subject: Update_Subject):
    print("Updating subject:", subject)

    # Find the subject by ID
    existing_subject = await subject_collection.find_one({"subject_id": subject.subject_id})

    if not existing_subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    # Update the subject name
    result = await subject_collection.update_one(
        {"subject_id": subject.subject_id},  # Find the subject by ID
        {"$set": {"subject_name": subject.subject_name}}  # Update the subject name
    )

    if result.modified_count == 1:
        return {"message": "Subject updated successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to update Subject")

@app.delete("/delete_subject/{subject_id}")
async def delete_subject(subject_id: int):
    try:
        # Check if the subject exists
        existing_subject = await subject_collection.find_one({"subject_id": subject_id})
        if not existing_subject:
            raise HTTPException(status_code=404, detail="Subject not found")

        # Perform the delete operation
        await subject_collection.delete_one({"subject_id": subject_id})

        return {"message": "Subject deleted successfully"}
    except Exception as e:
        print(f"Unhandled Exception: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")



class Topic(BaseModel):
    topicName: str
    className: str
    subjectName: str
    mediumName: str
    boardName: str

@app.post("/add_topic")
async def add_topic(topic: Topic):
    # Check if the topic already exists with the same subject, class, medium, and board
    existing_topic = await topic_collection.find_one({
        "topic_name": topic.topicName,
        "class_id": topic.className,
        "subject_id": topic.subjectName,
        "medium_id": topic.mediumName,
        "board_id": topic.boardName
    })
    if existing_topic:
        return {"message": "Topic already exists"}

    # Find the last inserted topic ID
    last_record = await topic_collection.find_one(sort=[("topic_id", DESCENDING)])

    # If no records exist, start with ID 1
    if last_record:
        new_id = last_record["topic_id"] + 1
    else:
        new_id = 1

    # Create the topic profile data
    topic_profile = {
        "topic_name": topic.topicName,
        "topic_id": new_id,
        "class_id": topic.className,
        "subject_id": topic.subjectName,
        "medium_id": topic.mediumName,
        "board_id": topic.boardName
    }

    # Insert the new topic into the collection
    await topic_collection.insert_one(topic_profile)

    return {"message": "Topic added successfully"}

class TopicDtl(BaseModel):
    className: str
    mediumName: str
    boardName: str
    subjectName: str


@app.post("/get_TopicDetails")
async def topic_details(top: TopicDtl):
    print(top)
    try:
        # Fetch the subjects from MongoDB
        topics = await topic_collection.find({
            "class_id": top.className,
            "medium_id": top.mediumName,
            "board_id": top.boardName,
            "subject_id": top.subjectName
        }).to_list(length=None)

        # Convert ObjectId to string
        for topic in topics:
            if "_id" in topic:
                topic["_id"] = str(topic["_id"])  # Convert ObjectId to string

        return topics

    except Exception as e:
        print(f"Unhandled Exception: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

@app.get("/get_TopicDetails1")
async def get_topic_details(request: Request):
    try:
        # Fetch all subjects
        cursor = topic_collection.find()
        topics = await cursor.to_list(length=None)

        # Create a list to store detailed subject information
        detailed_topics = []

        # Iterate through subjects and fetch related class, medium, and board details
        for topic in topics:
            topic["_id"] = str(topic["_id"])  # Convert ObjectId to string

            # Fetch the subject_id directly
            topic_id = topic.get("topic_id", "Unknown topic_ID")
            # Convert class_id, medium_id, and board_id to int for the query

            try:
                class_id = int(topic.get("class_id", 0))
                medium_id = int(topic.get("medium_id", 0))
                board_id = int(topic.get("board_id", 0))
                subject_id = int(topic.get("subject_id",0))
            except ValueError:
                print(f"Invalid ID format for subject {topic['_id']}")
                class_id, medium_id, board_id, subject_id = None, None, None, None

            # print(f"Subject ID: {subject['_id']}")
            # print(f"Class ID: {class_id} (Type: {type(class_id)})")
            # print(f"Medium ID: {medium_id} (Type: {type(medium_id)})")
            # print(f"Board ID: {board_id} (Type: {type(board_id)})")

            # Fetch class name based on class_id
            class_data = await class_collection.find_one({"classs_id": class_id})
            topic["class_name"] = class_data["classs_name"] if class_data else "Unknown Class"
            if not class_data:
                print(f"No class found for class_id: {class_id}")

            # Fetch medium name based on medium_id
            medium_data = await medium_collection.find_one({"medium_id": medium_id})
            topic["medium_name"] = medium_data["medium_name"] if medium_data else "Unknown Medium"
            if not medium_data:
                print(f"No medium found for medium_id: {medium_id}")

            # Fetch board name based on board_id
            board_data = await board_collection.find_one({"board_id": board_id})
            topic["board_name"] = board_data["board_name"] if board_data else "Unknown Board"
            if not board_data:
                print(f"No board found for board_id: {board_id}")
            
            subject_data = await subject_collection.find_one({"subject_id": subject_id})
            topic["subject_name"] = subject_data["subject_name"] if subject_data else "Unknown Subject"
            if not board_data:
                print(f"No board found for subject_id: {subject_id}")

            # Append the subject with the fetched details
            detailed_topics.append({
                "_id": topic["_id"],
                "topic_id": topic_id,  # Add subject_id here
                "topic_name": topic["topic_name"],
                "subject_name": topic["subject_name"],
                "class_name": topic["class_name"],
                "medium_name": topic["medium_name"],
                "board_name": topic["board_name"]
            })

        return detailed_topics
    

    except Exception as e:
        print(f"Unhandled Exception: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")
    
class Update_Topic(BaseModel):
    topic_id: int
    topic_name: str

@app.put("/update_topic")
async def update_topic(topic: Update_Topic):
    print("Updating topic:", topic)

    # Find the topic by ID
    existing_topic = await topic_collection.find_one({"topic_id": topic.topic_id})

    if not existing_topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # Update the topic name
    result = await topic_collection.update_one(
        {"topic_id": topic.topic_id},  # Find the topic by ID
        {"$set": {"topic_name": topic.topic_name}}  # Update the topic name
    )

    if result.modified_count == 1:
        return {"message": "Topic updated successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to update Topic")
    
    
@app.delete("/delete_topic/{topic_id}")
async def delete_topic(topic_id: int):
    try:
        # Check if the topic exists
        existing_topic = await topic_collection.find_one({"topic_id": topic_id})
        if not existing_topic:
            raise HTTPException(status_code=404, detail="Topic not found")

        # Perform the delete operation
        await topic_collection.delete_one({"topic_id": topic_id})

        return {"message": "Topic deleted successfully"}
    except Exception as e:
        print(f"Unhandled Exception: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

    
# LOGout part
@app.get("/")
async def read_root(request: Request):
    # Example endpoint
    return {"message": "Welcome to the Admin Dashboard"}

@app.get("/logout")
async def logout(request: Request):
    request.session.pop("user", None)  # Remove user from session
    return RedirectResponse(url="/static/login.html")

@app.get("/login.html")
async def login():
    # Serve the login page (static file or template)
    return {"message": "Login Page"}

class ForgotPasswordRequest(BaseModel):
    email: str
    instituteId: str
    role: str
    dob: str = None  # Optional, only required for students

@app.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    print("thaats is request",request)
    user = await profiles_collection.find_one({
        "email": request.email,
        "institute_id": request.instituteId,
        "role": request.role
    })

    print(user)

    if not user:
        raise HTTPException(status_code=404, detail="Profile not found with the given email, and institute ID")
    
    if user:
        if request.role == "student" and user.get("date_of_birth") != request.dob:
            raise HTTPException(status_code=400, detail="Invalid credentials")
    
    if "_id" in user:
        user["_id"] = str(user["_id"])  # Convert ObjectId to string
    

    # If valid, allow reset password (or send token/email)
    return {"success": True, "message": "User verified. You can reset your password.","user":user}

# Pydantic model for reset password request
class ResetPasswordRequest(BaseModel):
    email: str
    role: str  # Include this if necessary
    newPassword: str

@app.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    print(f"Received request to reset password for: {request.email}")
    user = await auth_collection.find_one({"email": request.email})
    
    if not user:
        print(f"User with email {request.email} not found")
        raise HTTPException(status_code=404, detail="User not found")
    
    # Hash the new password
    hashed_password = pwd_context.hash(request.newPassword)
    await auth_collection.update_one({"email": request.email}, {"$set": {"password": hashed_password}})
    
    return {"success": True, "message": "Password reset successfully."}

    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)