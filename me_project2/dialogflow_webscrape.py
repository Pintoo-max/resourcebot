import requests
from bs4 import BeautifulSoup
import re
import json
from typing import Dict
from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
from pymongo import MongoClient
from urllib.parse import quote_plus

from replacements import replace_names, replacements
from datetime import datetime, timedelta

app = FastAPI()

# MongoDB connection setup
username = quote_plus("rvscret")  # Replace with your MongoDB username
password = quote_plus("Runthistown%401")  # Replace with your MongoDB password
connection_string = f"mongodb+srv://rvscret:Runthistown%401@bankinfo.b85dspa.mongodb.net/"  # Adjust as necessary
client = MongoClient(connection_string)
db = client['bank_info']  # Replace with your database name
collection = db['IFSC_logs']  # Replace with your collection name

# current_timestamp = datetime.now()



@app.post("/")
async def handle_request(request: Request):
    # Retrieve the JSON data from the request
    payload = await request.json()
    # retrive the name of the intent
    intent = payload['queryResult']['intent']['displayName']

    # get district name from parameters
    district_query = payload['queryResult']['parameters'].get('district_name', None)
    if district_query:
        district_query = district_query.upper()
        print(district_query)

    # get bank name from paramenetrs
    bank_query = payload['queryResult']['parameters'].get('bank_name', None)
    print(bank_query)

    # state_query = payload['queryResult']['parameters']['state_name']
    # state_query = state_query.upper()
    # print(state_query)


# -- -- -- -- CONDITION ( LIST BANKS ) -- -- -- -- 

    if intent == "list_bank_execute":

        return get_banks_with_district(district_query)
    
# -- -- -- -- CONDITION ( BANK SEARCH ) -- -- -- --

    elif intent == "filter_bank_district":

        return filter_banks_with_district(bank_query, district_query)
    
# -- -- -- -- CONDITION ( IFSC SEARCH ) -- -- -- --

    elif intent == "ifsc_inputs_from_users":
        print("You are in intent: ifsc_inputs_from_users")

        # retrive the parameters from diagonistics from dialog flow
        parameters = payload['queryResult']['parameters']
        # list the parameter values
        parameters_value = list(parameters.values())
        # extract ifsc code
        cleaned_ifsc_codes = [code for code in parameters_value if code]
        # cleaned ifsc code
        cleaned_ifsc_codes1 = cleaned_ifsc_codes[0]
        print(f"IFSC Code: {cleaned_ifsc_codes1}")

        # Get existing data from the document based on ifsc
        existing_data = collection.find_one({'IFSC':cleaned_ifsc_codes1})

        if existing_data:
            # get timestamp from the document
            timestamp_str = existing_data.get('TIMESTAMP', '')

            if timestamp_str != "":
                # Get document timestamp
                document_timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                # Get the current timestamp
                current_timestamp = datetime.now()


            if existing_data.get('BANK') == "" or existing_data.get('BRANCH_TIMINGS') == "" or 'TIMESTAMP' not in existing_data or current_timestamp - document_timestamp > timedelta(days=30):
                # get scrape url from the document
                scrape_url = existing_data.get('URL')
                print("Condition Full Web Scrape")
                # condition = "fresh_scrape"
                return web_scrapes_next(scrape_url, cleaned_ifsc_codes1)

            elif all(field in existing_data and existing_data[field] not in [None, ""] for field in existing_data.keys() if field not in ['IFSC', 'URL', 'BRANCH_CODE', 'MICR', 'PINCODE', 'TIMESTAMP']):
                print("Condition mongodb extraction")
                return mongodb_extraction(existing_data)
            
                
# -- -- -- -- FUNCTION ( To extract data from mongodb ) -- -- -- --           
def mongodb_extraction(existing_data):

    db_extract_with_info = {
        "Bank": existing_data['BANK'],
        "IFSC": existing_data['IFSC'],
        "MICR Code": existing_data['MICR'],
        "Branch": existing_data['BRANCH'],
        "Branch Code": existing_data['BRANCH_CODE'],
        "Centre": existing_data['CENTRE'],
        "District": existing_data['DISTRICT'],
        "State": existing_data['STATE'],
        "Address": existing_data['ADDRESS'],
        "City": existing_data['CITY'],
        "Branch Timings": existing_data['BRANCH_TIMINGS'],
        "Contact Number": existing_data['CONTACT'],
        "Fax Number": existing_data['FAX'],
        "Toll Free": existing_data['TOLL'],
        "Official Website": existing_data['OFFICIAL_WEBSITE'],
        "Bank Email": existing_data['BANK_EMAIL'],

    }

    processed_db_extract = "\n".join([f"{key}: {value}" for key, value in db_extract_with_info.items()])
    # print(processed_db_extract)

    return JSONResponse(content={
        "fulfillmentText": processed_db_extract
    })


# -- -- -- -- FUNCTION ( WEBSCRAPING ) -- -- -- --  
def web_scrapes_next(scrape_url, cleaned_ifsc_code1):
    # second_url = modified_url
    # print(f"This is your condition is: {condition} ")
    response1 = requests.get(scrape_url)
    html_content1 = response1.content

    # Step 2: Parse the HTML content
    soup1 = BeautifulSoup(html_content1, 'html.parser')

    paragraphs1 = soup1.find_all('p')
    text_data1 = [para1.get_text() for para1 in paragraphs1]
    # print("This is textdata1")
    # print(text_data1)

    potential_email_elements = soup1.find_all(string=re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'))

    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

    extracted_emails = re.findall(email_pattern, str(potential_email_elements))

    filtered_text_data = [line for line in text_data1 if "[email protected]" not in line]

    # print(filtered_text_data)

    # Step 5: Organize the data into a readable format
    organized_data = '\n'.join(filtered_text_data)
    if extracted_emails:
        organized_data += f'\nBank Emails: {", ".join(extracted_emails)}'

    # Regular expressions to match the required fields
    bank_name = re.search(r"Bank Name:\s*(.+)", organized_data)
    ifsc = re.search(r"IFSC Code:\s*(.+)", organized_data)
    micr = re.search(r"MICR Code:\s*(.+)", organized_data)
    branch_name = re.search(r"Branch Name:\s*(.+)", organized_data)
    branch_code = re.search(r"Branch Code:\s*(.+)", organized_data)
    district = re.search(r"District:\s*(.+)", organized_data)
    state = re.search(r"State:\s*(.+)", organized_data)
    address = re.search(r"Address:\s*(.+)", organized_data)
    city = re.search(r"City:\s*(.+)", organized_data)
    contact_number = re.search(r"Contact Number:\s*([0-9-]+)", organized_data)
    fax_number = re.search(r"Fax Number:\s*([0-9-]+)", organized_data)
    toll_free_number = re.search(r"Toll Free Number:\s*([0-9 ,]+)", organized_data)
    official_website = re.search(r"Official Website:\s*(\S+)", organized_data)
    bank_emails = re.search(r"Bank Emails:\s*(\S+)", organized_data)
    branch_timings = re.search(r"Branch Timings:\s*(.+)", organized_data)

    # Extract the values
    bank_name = bank_name.group(1) if bank_name else "N/A"
    ifsc = ifsc.group(1) if ifsc else "N/A"
    micr = micr.group(1) if micr else "N/A"
    branch_name = branch_name.group(1) if branch_name else "N/A"
    branch_code = branch_code.group(1) if branch_code else "N/A"
    district = district.group(1) if district else "N/A"
    state = state.group(1) if state else "N/A"
    address = address.group(1) if address else "N/A"
    city = city.group(1) if city else "N/A"
    contact_number = contact_number.group(1) if contact_number else "N/A"
    fax_number = fax_number.group(1) if fax_number else "N/A"
    toll_free_number = toll_free_number.group(1) if toll_free_number else "N/A"
    official_website = official_website.group(1) if official_website else "N/A"
    bank_emails = bank_emails.group(1) if bank_emails else "N/A"
    branch_timings = branch_timings.group(1) if branch_timings else "N/A"

    # Get the current timestamp
    current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # dict for data upload to mongodb
    join_data_full = {

        "BANK": bank_name,
        "BRANCH": branch_name,
        "MICR": micr,
        "BRANCH_CODE": branch_code,
        "CENTRE": district,
        "DISTRICT": district,
        "STATE": state,
        "ADDRESS": address,
        "CITY": city,
        "BRANCH_TIMINGS": branch_timings,  
        "CONTACT": contact_number,
        "FAX": fax_number,
        "TOLL": toll_free_number,
        "OFFICIAL_WEBSITE": official_website,
        "BANK_EMAIL": bank_emails,
        "TIMESTAMP": current_timestamp,

    }

    # Format the extracted values
    formatted_data1_full = (
        f"Bank Name: {bank_name}\n"
        f"IFSC: {cleaned_ifsc_code1}\n"
        f"MICR Code: {micr}\n"
        f"Branch Name: {branch_name}\n"
        f"Branch Code: {branch_code}\n"
        f"District: {district}\n"
        f"State: {state}\n"
        f"Address: {address}\n"
        f"City: {city}\n"
        f"Branch Timings: {branch_timings}\n"
        f"Contact Number: {contact_number}\n"
        f"Fax Number: {fax_number}\n"
        f"Toll Free Number: {toll_free_number}\n"
        f"Official Website: {official_website}\n"
        f"Bank Emails: {bank_emails}"
    )

    # query to update document in mongodb
    result = collection.update_one(
            {"IFSC": cleaned_ifsc_code1},
            {"$set": join_data_full}
        )
    return JSONResponse(content={
        "fulfillmentText": formatted_data1_full
    })

# -- -- -- -- FUNCTION ( To search specific bank in a specific area ) -- -- -- --  
def filter_banks_with_district(bank_query, district_query):

    # banks_in_state = search_address_keyword(bank_query, district_query)

    regex = {"$regex": district_query, "$options": "i"}
    
    # Query to find documents with the specific bank and address containing the keyword
    documents = collection.find(
        {"BANK": bank_query, "ADDRESS": regex},
        {"IFSC": 1, "BRANCH": 1, "ADDRESS": 1, "_id": 0}
    )
    
    # Convert the cursor to a list of documents
    result_docs = list(documents)

    formatted_data = ""
    for entry in result_docs:
        formatted_data += f"IFSC : {entry['IFSC']}\n"
        formatted_data += f"BRANCH : {entry['BRANCH']}\n"
        formatted_data += f"ADDRESS : {entry['ADDRESS']}\n\n"
    # print(formatted_data.strip())

    return JSONResponse(content={
            "fulfillmentText": formatted_data.strip()
        })

# -- -- -- -- FUNCTION ( To search specific word in address field of the document ) -- -- -- --  
# def search_address_keyword(bank_name, keyword):
#     # Use a regular expression to search for the keyword in the ADDRESS field (case-insensitive)
#     regex = {"$regex": keyword, "$options": "i"}
    
#     # Query to find documents with the specific bank and address containing the keyword
#     documents = collection.find(
#         {"BANK": bank_name, "ADDRESS": regex},
#         {"IFSC": 1, "BRANCH": 1, "ADDRESS": 1, "_id": 0}
#     )
    
#     # Convert the cursor to a list of documents
#     result_docs = list(documents)
#     return result_docs

# -- -- -- -- FUNCTION ( To list all banks in a specific area ) -- -- -- --  
def get_banks_with_district(district_query):

    print(f"You are filter district and this is your query : {district_query}")

    regex = {"$regex": district_query, "$options": "i"}
    
    # Query to find documents with the address containing the keyword
    documents = collection.find(
        {"ADDRESS": regex},
        {"BANK": 1, "_id": 0}
    )
    
    # Extract unique bank names
    list_banks = {doc['BANK'] for doc in documents}

    # list_banks = list_banks_by_address_keyword(district_query)

    list_banks = "\n".join(list_banks)

    # print("This is bank search with keywords")
    print("List banks executed")

    return JSONResponse(content={
            "fulfillmentText": list_banks
        })

# -- -- -- -- FUNCTION ( To list all banks in a specific area ) -- -- -- --  
# def list_banks_by_address_keyword(keyword):
#     # Use a regular expression to search for the keyword in the ADDRESS field (case-insensitive)
#     regex = {"$regex": keyword, "$options": "i"}
    
#     # Query to find documents with the address containing the keyword
#     documents = collection.find(
#         {"ADDRESS": regex},
#         {"BANK": 1, "_id": 0}
#     )
    
#     # Extract unique bank names
#     banks = {doc['BANK'] for doc in documents}
#     return list(banks)