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

app = FastAPI()

# MongoDB connection setup
username = quote_plus("rvscret")  # Replace with your MongoDB username
password = quote_plus("Runthistown%401")  # Replace with your MongoDB password
connection_string = f"mongodb+srv://rvscret:Runthistown%401@bankinfo.b85dspa.mongodb.net/"  # Adjust as necessary
client = MongoClient(connection_string)
db = client['bank_info']  # Replace with your database name
collection = db['IFSC_logs']  # Replace with your collection name


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
    # print(cleaned_ifsc_codes1)

    district_query = payload['queryResult']['parameters']['district_name']
    district_query = district_query.upper()
    print(district_query)

    state_query = payload['queryResult']['parameters']['state_name']
    state_query = state_query.upper()
    print(state_query)

    bank_query = payload['queryResult']['parameters']['bank_name']
    bank_query = bank_query
    print(bank_query)

    existing_data = collection.find_one({'IFSC':cleaned_ifsc_codes1})
    # print(existing_data)

    # if intent == "list_banks":

    return list_all_banks(bank_query, district_query)


    # if existing_data['BANK'] == "Ahmednagar District Central Co-operative Bank":
    #     print("You are in Bank if")

    #     db_extract_with_info = {
    #         "IFSC": existing_data['IFSC'],
    #         "Bank": existing_data['BANK'],
    #         "Branch": existing_data['BRANCH'],
    #         "Centre": existing_data['CENTRE'],
    #         "District": existing_data['DISTRICT'],
    #         "State": existing_data['STATE'],
    #         "Address": existing_data['ADDRESS'],
    #         "City": existing_data['CITY'],
    #         "Contact": existing_data.get('CONTACT'),
    #         "Toll Free": existing_data.get('TOLL'),
    #         "Official Website": existing_data.get('OFFICIAL_WEBSITE'),
    #         "Bank Email": existing_data.get('BANK_EMAIL'),  

    #     }

    #     processed_db_extract = "\n".join([f"{key}: {value}" for key, value in db_extract_with_info.items()])
    #     # print(processed_db_extract)

    #     return JSONResponse(content={
    #         "fulfillmentText": processed_db_extract
    #     })

    # elif "BANK_EMAIL" and "OFFICIAL_WEBSITE" and "TOLL" and "CONTACT" in existing_data:
    #     print("MongoBD extraction Executed")
        
    #     db_extract_with_info = {
    #         "IFSC": existing_data['IFSC'],
    #         "Bank": existing_data['BANK'],
    #         "Branch": existing_data['BRANCH'],
    #         "Centre": existing_data['CENTRE'],
    #         "District": existing_data['DISTRICT'],
    #         "State": existing_data['STATE'],
    #         "Address": existing_data['ADDRESS'],
    #         "City": existing_data['CITY'],
    #         "Contact": existing_data['CONTACT'],
    #         "Toll Free": existing_data['TOLL'],
    #         "Official Website": existing_data['OFFICIAL_WEBSITE'],
    #         "Bank Email": existing_data['BANK_EMAIL'],

    #     }

    #     processed_db_extract = "\n".join([f"{key}: {value}" for key, value in db_extract_with_info.items()])
    #     # print(processed_db_extract)

    #     return JSONResponse(content={
    #         "fulfillmentText": processed_db_extract
    #     })
    
    # else:

    #     # return print("You are at else")

    #     return web_scrapes(cleaned_ifsc_codes1)

# def get_branches_by_district(bank_name, district):
#     documents = collection.find({"BANK": bank_name, "DISTRICT": district}, {"BRANCH": 1, "_id": 0})
#     branches = {doc['BRANCH'] for doc in documents}
#     return list(branches)

# def get_districts_by_state(bank_name, state):
#     documents = collection.find({"BANK": bank_name, "STATE": state}, {"DISTRICT": 1, "_id": 0})
#     districts = {doc['DISTRICT'] for doc in documents}
#     return list(districts)

# def get_banks_by_city(bank_name, city):
#     documents = collection.find({"BANK": bank_name, "CITY": city})
#     return list(documents)

# def get_banks_by_centre(bank_name, centre):
#     documents = collection.find({"BANK": bank_name, "CENTRE": centre})
#     return list(documents)

# def get_banks_by_centre(bank_name, centre):
#     documents = collection.find({"BANK": bank_name, "CENTRE": centre})
#     return list(documents)

# def get_banks_by_district_general(district):
#     documents = collection.find({"DISTRICT": district})
#     return list(documents)

# def get_banks_by_state_general(state):
#     documents = collection.find({"STATE": state})
#     return list(documents)

# def get_banks_by_city_general(city):
#     documents = collection.find({"CITY": city})
#     return list(documents)

# def get_banks_by_centre_general(centre):
#     documents = collection.find({"CENTRE": centre})
#     return list(documents)

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
    bank_name = text_data[7].replace("CO-OPERATIVE", "COOPERATIVE")
    state_name = text_data[8]
    district_name = text_data[9]
    branch_name = text_data[11]
    ifsc_code = text_data[12]

    first_url =  f'https://www.askbankifsccode.com/{bank_name}/{state_name}/{district_name}/{branch_name}-{ifsc_code}'
    modified_url = first_url.replace(" ", "-").replace(",", "-")
    print(modified_url)

    return web_scrapes_next(modified_url, ifsc_code)

def web_scrapes_next(modified_url, ifsc_code):
    second_url = modified_url

    response1 = requests.get(second_url)
    html_content1 = response1.content

    # Step 2: Parse the HTML content
    soup1 = BeautifulSoup(html_content1, 'html.parser')

    paragraphs1 = soup1.find_all('p')
    text_data1 = [para1.get_text() for para1 in paragraphs1]

    potential_email_elements = soup1.find_all(string=re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'))

    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

    extracted_emails = re.findall(email_pattern, str(potential_email_elements))

    filtered_text_data = [line for line in text_data1 if "[email protected]" not in line]

    # Step 5: Organize the data into a readable format
    organized_data = '\n'.join(filtered_text_data)
    if extracted_emails:
        organized_data += f'\nBank Emails: {", ".join(extracted_emails)}'

    # Regular expressions to match the required fields
    contact_number = re.search(r"Contact Number:\s*([0-9-]+)", organized_data)
    fax_number = re.search(r"Fax Number:\s*([0-9-]+)", organized_data)
    toll_free_number = re.search(r"Toll Free Number:\s*([0-9 ,]+)", organized_data)
    official_website = re.search(r"Official Website:\s*(\S+)", organized_data)
    bank_emails = re.search(r"Bank Emails:\s*(\S+)", organized_data)

    # Extract the values
    contact_number = contact_number.group(1) if contact_number else "N/A"
    fax_number = fax_number.group(1) if fax_number else "N/A"
    toll_free_number = toll_free_number.group(1) if toll_free_number else "N/A"
    official_website = official_website.group(1) if official_website else "N/A"
    bank_emails = bank_emails.group(1) if bank_emails else "N/A"

    # webscrape dict
    join_data = {
        "CONTACT": contact_number,
        "TOLL": toll_free_number,
        "OFFICIAL_WEBSITE": official_website,
        "BANK_EMAIL": bank_emails,  
    }

    # Format the extracted values
    formatted_data1 = (
        f"Contact Number: {contact_number}\n"
        f"Fax Number: {fax_number}\n"
        f"Toll Free Number: {toll_free_number}\n"
        f"Official Website: {official_website}\n"
        f"Bank Emails: {bank_emails}"
    )

    # mongodb extract query
    existing_data1 = collection.find_one({'IFSC':ifsc_code})

    # mongodb extract
    db_extract_no_info = {
    "IFSC": existing_data1['IFSC'],
    "Bank": existing_data1['BANK'],
    "Branch": existing_data1['BRANCH'],
    "Centre": existing_data1['CENTRE'],
    "District": existing_data1['DISTRICT'],
    "State": existing_data1['STATE'],
    "Address": existing_data1['ADDRESS'],
    "City": existing_data1['CITY'],

    }

    # mongodb extract in str
    formatted_data2 = "\n".join([f"{key}: {value}" for key, value in db_extract_no_info.items()])

    # mongodb extract str + webscrape str
    formatted_data3 = formatted_data2 + formatted_data1

    if formatted_data3 == "":
        return JSONResponse(content={
            "fulfillmentText": f"Sorry!!!, IFSC Code: {ifsc_code} does not exist!"
        })
    
    else:
        print("Webscraping Executed")

        result = collection.update_one(
            {"IFSC": ifsc_code},
            {"$set": join_data}
        )
        return JSONResponse(content={
            "fulfillmentText": formatted_data3
        })

def list_all_banks(bank_query, district_query):
        # Query to find all documents
    # documents = collection.find({"DISTRICT":district_query}, {"BANK": 1, "_id": 0})

    # banks_in_state = list_banks_by_address_keyword("VIKHROLI")
    banks_in_state = search_address_keyword(bank_query, district_query)

    print("This is bank search with keywords")
    print(banks_in_state)

    # # Extract bank values and store them in a list
    # bank_values = {doc['BANK'] for doc in documents}

    # unique_bank_values = list(bank_values)
    # # print(unique_ifsc_values)

    # bank_values_string = "\n".join(unique_bank_values)

    # # Store the result in a variable
    # output_variable = bank_values_string

    # # Print the result
    # print("-- -- -- -- This is District bank -- -- -- --")
    # print(output_variable)
    # # Print the IFSC values
    # # print(unique_bank_values)

    # result_docs = list(documents)

    # # Print the results
    # for doc in result_docs:
    #     print(doc)

    return JSONResponse(content={
            "fulfillmentText": "You are in list banks"
        })


