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
database = client.State_Board
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

def get_collection(class_name: str) -> Collection:
    collection_name = f"class_{class_name}"
    print(collection_name)
    return database[collection_name]


app.mount("/static", StaticFiles(directory="static"), name="static")

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

@app.post("/submit")
async def form_uplaod(
    board: str = Form(...),
    medium: str = Form(...),
    grade: str = Form(...),
    subject: str = Form(...),
    lesson: str = Form(...),
    tasks: str = Form(...),
    file: UploadFile = File(...),
   ):
   
    print(board)
    print(medium)
    print("This is subject")
  
    if tasks=='text-book-solution':
        print(tasks)
        unique_code = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        new_filename = f"{board}_{medium}_{grade}_{subject}_{lesson}_{tasks}"
        pdffilename = f"{board}_{medium}_{grade}_{subject}_{lesson}_{tasks}.pdf"
        print(new_filename)

        print("Generated filename:", pdffilename)

        # Ensure the upload folder exists
        upload_folder = 'upload/textbook_pdf'
        file_path = os.path.join(upload_folder, pdffilename)
      # print("file path name", file_path)
       # file.save(file_path)

       # Save the file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        print("File uploaded successfully:", pdffilename)

        existing_grade = await class_collection.find_one({"classs_id": int(grade)})
        print(existing_grade)
        class_name = existing_grade["classs_name"]

        collection = get_collection(class_name)
        print(collection)

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
                "file_path": file_path
            }
        result = await collection.insert_one(document)
        print("Document to insert:", document)

        print("This is detect formatresult collection")
        print(result)
        return {"file_id": str(result.inserted_id), "message": "File uploaded and saved successfully", "filename": new_filename}

       



    else:
        file_contents = await file.read()
        file_extension = file.filename.split('.')[-1].lower()
        print(file_extension)

        if file_extension == 'pdf':
            text = extract_text_from_pdf(file_contents)
        elif file_extension in ['doc', 'docx']:
            text = extract_text_from_doc(file_contents)
            print(text)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        tasks_list = tasks.split(",")  # Assuming tasks are sent as a comma-separated string
        
        # Generate a unique code and timestamp
        unique_code = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

        print("this is something")
        existing_board = await board_collection.find_one({"board_id": int(board)})
        print(existing_board)
        board_name = existing_board["board_name"]
        
        existing_medium = await medium_collection.find_one({"medium_id": int(medium) })
        print(existing_medium)
        medium_name = existing_medium["medium_name"]

        existing_grade = await class_collection.find_one({"classs_id": int(grade)})
        print(existing_grade)
        class_name = existing_grade["classs_name"]

        existing_subject = await subject_collection.find_one({"subject_id": int(subject) })
        print(existing_subject)
        subject_name = existing_subject["subject_name"]

        existing_topic = await topic_collection.find_one({"topic_id": int(lesson) })
        print(existing_topic)
        topic_name = existing_topic["topic_name"]

        new_filename = f"{board_name[:3]}_{medium_name[:3]}_{class_name}_{subject_name[:3]}_{topic_name}_{'.'.join(tasks_list)}"
        #new_filename = f"{board}{medium}{grade}{subject}{lesson}_{'.'.join(tasks_list)}"
        print(new_filename)

        # new_filename = f"{board}_{medium}_{grade}_{subject}_{lesson}_{'.'.join(tasks_list)}"
        # new_filename = f"{board_name[:3]}{medium_name[:3]}{grade}{subject_name[:3]}{lesson}_{'.'.join(tasks_list)}"

        print("Generated filename:", new_filename)

        print("This is collection2")
        collection = get_collection(class_name)
        print(collection)


        # Check for existing files with the same base filename
        existing_file = await collection.find_one({"filename": new_filename})

        if existing_file:
            print("This is existing file")
            # print(existing_file)
            # Extract existing questions and answers
            existing_data = existing_file.get('questions_and_answers', {})

            print("this is filename",new_filename)
            # Parse new questions and answers
            new_data = parse_questions_and_answers(text, new_filename)
            
            print("This is new_data")
            print(new_data)

            
            if new_data:
                # if 'question' in new_data:
                    # Find the maximum existing question number in the document
                max_question_num = max(
                [int(key.replace('question', '')) for key in existing_data.keys() if key.startswith('question')] or [0])

                # Prepare cleaned data by excluding unnecessary keys like heading and filename
                cleaned_new_data = {}
                for key, value in new_data.items():
                    # if key.startswith('heading') or key == 'filename':
                    #     continue  # Skip the heading and filename
                    cleaned_new_data[key] = value

                    if len(cleaned_new_data) % 2 == 0:
                        num_questions = len(cleaned_new_data) // 2
                        # print("gljwe    wiyefijb",tasks_list)
                        print(f"tasks_list: {tasks_list}")
                        if not any(task in tasks_list for task in ['match-the-column', 'multiple-choice-questions', 'true-false']):
                            print("'match-the-column' not in tasks_list, proceeding with question and answer processing...")
                            for i in range(1, num_questions + 1):
                                question_key = f"question{i}"
                                answer_key = f"answer{i}"
                                
                                new_question_key = f"question{max_question_num + i}"
                                new_answer_key = f"answer{max_question_num + i}"
                            
                                if question_key in cleaned_new_data and answer_key in cleaned_new_data:
                                    existing_data[new_question_key] = cleaned_new_data[question_key]
                                    existing_data[new_answer_key] = cleaned_new_data[answer_key]
                                
                            # Update the existing document in MongoDB
                            results = await collection.update_one(
                                {"_id": existing_file["_id"]},
                                {"$set": {
                                    "questions_and_answers": existing_data,
                                    "timestamp": timestamp  # Update the timestamp
                                }}
                            )
                            print(results)
                        else:
                            print("No questions and answers extracted or incorrect number of keys.")


                    if len(cleaned_new_data) % 4 == 0:
                        num_questions = len(cleaned_new_data) // 4
                    
                        if "multiple-choice-questions" in tasks_list:
                            print("Handling multiple-choice questions")
                            for i in range(1, num_questions + 1):
                                question_key = f"question{i}"
                                options_key = f"options{i}"
                                answer_key = f"answer{i}"
                                explanation_key = f"explanation{i}"
                                
                                new_question_key = f"question{max_question_num + i}"
                                new_options_key = f"options{max_question_num + i}"
                                new_answer_key = f"answer{max_question_num + i}"
                                new_explanation_key = f"explanation{max_question_num + i}"
                                
                                # Check if all required keys are in the new data
                                if question_key in cleaned_new_data:
                                    existing_data[new_question_key] = cleaned_new_data[question_key]
                                if options_key in cleaned_new_data:
                                    existing_data[new_options_key] = cleaned_new_data[options_key]
                                if answer_key in cleaned_new_data:
                                    existing_data[new_answer_key] = cleaned_new_data[answer_key]
                                if explanation_key in cleaned_new_data:
                                    existing_data[new_explanation_key] = cleaned_new_data[explanation_key]

                            # Update the existing document in MongoDB
                            results = await collection.update_one(
                                {"_id": existing_file["_id"]},
                                {"$set": {
                                    "questions_and_answers": existing_data,
                                    "timestamp": timestamp  # Update the timestamp
                                }}
                            )
                            print(results)
                        
                        elif "true-false" in tasks_list:
                            print("Handling true/false questions")
                            for i in range(1, num_questions + 1):
                                question_key = f"question{i}"
                                options_key = f"options{i}"
                                answer_key = f"answer{i}"
                                explanation_key = f"explanation{i}"
                                
                                new_question_key = f"question{max_question_num + i}"
                                new_options_key = f"options{max_question_num + i}"
                                new_answer_key = f"answer{max_question_num + i}"
                                new_explanation_key = f"explanation{max_question_num + i}"
                                
                                # Check if all required keys are in the new data
                                if question_key in cleaned_new_data:
                                    existing_data[new_question_key] = cleaned_new_data[question_key]
                                if options_key in cleaned_new_data:
                                    existing_data[new_options_key] = cleaned_new_data[options_key]
                                if answer_key in cleaned_new_data:
                                    existing_data[new_answer_key] = cleaned_new_data[answer_key]
                                if explanation_key in cleaned_new_data:
                                    existing_data[new_explanation_key] = cleaned_new_data[explanation_key]

                            # Update the existing document in MongoDB
                            results = await collection.update_one(
                                {"_id": existing_file["_id"]},
                                {"$set": {
                                    "questions_and_answers": existing_data,
                                    "timestamp": timestamp  # Update the timestamp
                                }}
                            )
                            print(results)

                        elif "match-the-column" in tasks_list:
                            print("Handling match-the-column questions")
                            for i in range(1, num_questions + 1):
                                question_key = f"question{i}"
                                column_a_key = f"column_a{i}"
                                column_b_key = f"column_b{i}"
                                answer_key = f"answer{i}"  # Corrected key name
                                
                                # print("KEYY")
                                
                                new_question_key = f"question{max_question_num + i}"
                                new_column_a_key = f"column_a{max_question_num + i}"
                                new_column_b_key = f"column_b{max_question_num + i}"
                                new_answer_key = f"answer{max_question_num + i}"  # Corrected key name
                                
                                # print("jwkerwkjbe;")

                                if question_key in cleaned_new_data and column_a_key in cleaned_new_data and column_b_key in cleaned_new_data and answer_key in cleaned_new_data:
                                    existing_data[new_question_key] = cleaned_new_data[question_key]
                                    existing_data[new_column_a_key] = cleaned_new_data[column_a_key]
                                    existing_data[new_column_b_key] = cleaned_new_data[column_b_key]
                                    existing_data[new_answer_key] = cleaned_new_data[answer_key]

                            print("This is cleaned new data", cleaned_new_data)

                            # Update the existing document in MongoDB
                            print("This is existing data", existing_data)
                            results = await collection.update_one(
                                {"_id": existing_file["_id"]},
                                {"$set": {
                                    "questions_and_answers": existing_data,
                                    "timestamp": timestamp  # Update the timestamp
                                }}
                            )
                            print(results)

                        else:
                            print("No questions and answers extracted or incorrect number of keys.")
                        
        else:
            print("hgjhvj;ht;j")
            new_data = parse_questions_and_answers(text, new_filename) or {}
            # print('hello')
            # print('new  data extract',new_data)
            if not new_data:
                print("No data extracted. Check the extraction logic and data format.")

            document = {
                "board": board,
                "board_name": board_name,
                "medium": medium,
                "medium_name": medium_name,
                "grade": grade,
                "grade_name": class_name,
                "subject": subject,
                "subject_name": subject_name,
                "lesson": lesson,
                "lesson_name": topic_name,
                "filename": new_filename,
                "tasks": tasks_list,
                "unique_code": unique_code,
                "timestamp": timestamp,
                "questions_and_answers": new_data
            }
            result = await collection.insert_one(document)
            print("Document to insert:", document)

            print("This is detect formatresult collection")
            print(result)
            return {"file_id": str(result.inserted_id), "message": "File uploaded and saved successfully", "filename": new_filename}

    return {"message": "File content appended successfully", "filename": new_filename}
            
    
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
    

    existing_grade = await class_collection.find_one({"classs_id": int(grade)})
    print(existing_grade)
    class_name = existing_grade["classs_name"]

    # Construct the query
    query = {
        "board": board,
        "medium": medium,
        "grade": grade,
        "subject": subject,
        "lesson": lesson,
        "tasks": {"$in": tasks.split(",")}
    }

    print("Query:", query)
    
    # Get the collection based on grade
    collection = get_collection(class_name)
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
    existing_grade = await class_collection.find_one({"classs_id": int(grade)})
    print(existing_grade)
    class_name = existing_grade["classs_name"]

    collection = get_collection(class_name)
   # print(collection)
    # Get the collection based on grade
   
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

# Login part start here

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
    
@app.post("/register")
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

    existing_user = await profiles_collection.find_one({"role": user.role,
                                                        "email": user.email,
                                                        "class_name":user.class_name,
                                                        "institute_id": user.institute_id,
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

@app.post("/student-teacher-login")
async def student_teacher_login(data: StudentTeacherLoginData):
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