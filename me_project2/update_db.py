import pymongo
from pymongo import MongoClient
import re
from urllib.parse import quote_plus

# MongoDB connection setup
username = quote_plus("rvscret")  # Replace with your MongoDB username
password = quote_plus("Runthistown%401")  # Replace with your MongoDB password
connection_string = f"mongodb+srv://rvscret:Runthistown%401@bankinfo.b85dspa.mongodb.net/"  # Adjust as necessary
client = MongoClient(connection_string)
db = client['bank_info']  # Replace with your database name
collection = db['IFSC_logs']  # Replace with your collection name

# Function to extract IFSC code from the URL
def extract_ifsc(url):
    match = re.search(r'-([A-Z0-9]+)$', url)
    if match:
        return match.group(1)
    return None

# Read URLs from data.txt
with open('data.txt', 'r', encoding='utf-8') as file:
    urls = file.readlines()

# Process each URL
for url in urls:
    url = url.strip()
    ifsc_code = extract_ifsc(url)
    if ifsc_code:
        # Update MongoDB document
        result = collection.update_one({'IFSC': ifsc_code}, {'$set': {'URL': url}})
        if result.matched_count:
            print(f"Updated document with IFSC: {ifsc_code}")
        else:
            print(f"No document found with IFSC: {ifsc_code}")

print("URL update process completed.")
