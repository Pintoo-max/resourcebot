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

app = FastAPI()

# MongoDB connection setup
username = quote_plus("rvscret")  # Replace with your MongoDB username
password = quote_plus("Runthistown%401")  # Replace with your MongoDB password
connection_string = f"mongodb+srv://rvscret:Runthistown%401@bankinfo.b85dspa.mongodb.net/"  # Adjust as necessary
client = MongoClient(connection_string)
db = client['bank_info']  # Replace with your database name
collection = db['IFSC_scrapes']  # Replace with your collection name

@app.post("/")
async def handle_request(request: Request):
    # Retrieve the JSON data from the request
    payload = await request.json()

    intent = payload['queryResult']['intent']['displayName']
    # print(intent)
    parameters = payload['queryResult']['parameters']
    # print(parameters)
    parameters_value = list(parameters.values())
    # print(parameters_value)
    cleaned_ifsc_codes = [code for code in parameters_value if code]
    # cleaned_ifsc_codes = cleaned_ifsc_codes[0]
    cleaned_ifsc_codes1 = cleaned_ifsc_codes[0]
    print(cleaned_ifsc_codes1)

    district_query = payload['queryResult']['parameters'].get('district_name', None)
    if district_query:
        district_query = district_query.upper()
        print(district_query)

    # state_query = payload['queryResult']['parameters']['state_name']
    # state_query = state_query.upper()
    # print(state_query)

    bank_query = payload['queryResult']['parameters'].get('bank_name', None)
    print(bank_query)

    # print(existing_data)

    if intent == "list_bank_execute":

        return get_banks_with_district(district_query)

    elif intent == "filter_bank_district":

        return filter_banks_with_district(bank_query, district_query)

    elif intent == "ifsc_inputs_from_users":
        existing_data = collection.find_one({'IFSC':cleaned_ifsc_codes1})

        scrape_url = existing_data.get('URL')

        if existing_data:

            if all(field in existing_data and existing_data[field] not in [None, ""] for field in existing_data.keys() if field not in ['IFSC', 'URL', 'BRANCH_CODE', 'MICR', 'PINCODE','TIMESTAMP']):
                # print("Condition mongodb extraction")
            
                db_extract_with_info = {
                    "Bank Name": existing_data['BANK'],
                    "IFSC Code": existing_data['IFSC'],
                    "MICR Code": existing_data['MICR'],
                    "Branch Name": existing_data['BRANCH'],
                    "Centre": existing_data['CENTRE'],
                    "District": existing_data['DISTRICT'],
                    "State": existing_data['STATE'],
                    "Address": existing_data['ADDRESS'],
                    "City": existing_data['CITY'],
                    "Branch Timings": existing_data['BRANCH_TIMINGS'],
                    "Contact Number": existing_data['CONTACT'],
                    "Fax Number" :existing_data['FAX'],
                    "Toll Free": existing_data['TOLL'],
                    "Official Website": existing_data['OFFICIAL_WEBSITE'],
                    "Bank Email": existing_data['BANK_EMAIL'],
                }

                processed_db_extract = "\n".join([f"{key}: {value}" for key, value in db_extract_with_info.items()])
                # print(processed_db_extract)

                print(f"MongoDB extraction executed for {cleaned_ifsc_codes1}")

                return JSONResponse(content={
                    "fulfillmentText": processed_db_extract
                })
            
            else:
                return web_scrapes_next(scrape_url, cleaned_ifsc_codes1)


def search_address_keyword(bank_name, keyword):
    # Use a regular expression to search for the keyword in the ADDRESS field (case-insensitive)
    regex = {"$regex": keyword, "$options": "i"}
    
    # Query to find documents with the specific bank and address containing the keyword
    documents = collection.find(
        {"BANK": bank_name, "ADDRESS": regex},
        {"IFSC": 1, "BRANCH": 1, "ADDRESS": 1, "_id": 0}
    )
    
    # Convert the cursor to a list of documents
    result_docs = list(documents)
    return result_docs

def list_banks_by_address_keyword(keyword):
    # Use a regular expression to search for the keyword in the ADDRESS field (case-insensitive)
    regex = {"$regex": keyword, "$options": "i"}
    
    # Query to find documents with the address containing the keyword
    documents = collection.find(
        {"ADDRESS": regex},
        {"BANK": 1, "_id": 0}
    )
    
    # Extract unique bank names
    banks = {doc['BANK'] for doc in documents}
    return list(banks)

def web_scrapes(cleaned_ifsc_codes1):
    # Step 1: Fetch the HTML content
    url = f"https://ifsc.bankifsccode.com/{cleaned_ifsc_codes1}"  # Replace with the actual URL
    print(url)
    response = requests.get(url)
    html_content = response.content

    # Step 2: Parse the HTML content
    soup = BeautifulSoup(html_content, 'html.parser')

    # For example, let's say we want to extract all the text inside <p> tags
    paragraphs = soup.find_all('a')
    text_data = [para.get_text() for para in paragraphs]

    bank_name = replace_names(text_data[7], replacements).replace("BANK LTD", "BANK").replace("THE ", "")
    
    # bank_name = text_data[7].replace("CO-OPERATIVE", "COOPERATIVE").replace("ABHYUDAYA CO-OP BANK LTD", "ABHYUDAYA COOPERATIVE BANK").replace("THE ANDHRA PRADESH STATE COOP BANK LTD", "ANDHRA-PRADESH-STATE-COOPERATIVE-BANK")
    state_name = text_data[8]
    district_name = replace_names(text_data[9], replacements)
    branch_name = replace_names(text_data[11], replacements).replace("(", "").replace(")", "").replace("BRANCH", "").strip()
    ifsc_code = text_data[12]

    first_url =  f'https://www.askbankifsccode.com/{bank_name}/{state_name}/{district_name}/{branch_name}-{ifsc_code}'
    modified_url = first_url.replace(" ", "-").replace(",", "-").replace(", ", "-").replace(". ", "-").replace("--", "-").replace(".-", "-").replace("-/", "/")
    print(modified_url)

    return web_scrapes_next(modified_url, ifsc_code)

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

    # print(organized_data)


    # Regular expressions to match the required fields
    bank_name = re.search(r"Bank Name:\s*(.+)", organized_data)
    ifsc = re.search(r"IFSC Code:\s*(.+)", organized_data)
    micr = re.search(r"MICR Code:\s*(.+)", organized_data)
    branch_name = re.search(r"Branch Name:\s*(.+)", organized_data)
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

    # if condition == "fresh_scrape":
    #     print("You are at fresh scrape!!!")
    
    join_data_full = {

        "BANK": bank_name,
        "BRANCH": branch_name,
        "MICR": micr,
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

    }

    # print(join_data_full)

        # Format the extracted values
    formatted_data1_full = (
        f"Bank Name: {bank_name}\n"
        f"IFSC Code: {cleaned_ifsc_code1}\n"
        f"MICR Code: {micr}\n"
        f"Branch Name: {branch_name}\n"
        f"Centre: {district}\n"
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

    result = collection.update_one(
            {"IFSC": cleaned_ifsc_code1},
            {"$set": join_data_full}
        )
    print(f"Web scrape executed for {cleaned_ifsc_code1}")
    return JSONResponse(content={
        "fulfillmentText": formatted_data1_full
    })


def filter_banks_with_district(bank_query, district_query):
        # Query to find all documents
    # documents = collection.find({"DISTRICT":district_query}, {"BANK": 1, "_id": 0})

    # banks_in_state = list_banks_by_address_keyword("VIKHROLI")
    banks_in_state = search_address_keyword(bank_query, district_query)

    # print("This is bank search with keywords")
    # print(banks_in_state)

    formatted_data = ""
    for entry in banks_in_state:
        formatted_data += f"IFSC : {entry['IFSC']}\n"
        formatted_data += f"BRANCH : {entry['BRANCH']}\n"
        formatted_data += f"ADDRESS : {entry['ADDRESS']}\n\n"
    print(formatted_data.strip())

    return JSONResponse(content={
            "fulfillmentText": formatted_data.strip()
        })

def get_banks_with_district(district_query):

    print(f"You are filter district and this is your query : {district_query}")
        # Query to find all documents
    # documents = collection.find({"DISTRICT":district_query}, {"BANK": 1, "_id": 0})

    # banks_in_state = list_banks_by_address_keyword("VIKHROLI")
    list_banks = list_banks_by_address_keyword(district_query)

    list_banks = "\n".join(list_banks)

    # print("This is bank search with keywords")
    print("List banks executed")

    return JSONResponse(content={
            "fulfillmentText": list_banks
        })

