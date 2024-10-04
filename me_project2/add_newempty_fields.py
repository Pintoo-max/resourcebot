import pymongo
from pymongo import MongoClient
from datetime import datetime
import re

from urllib.parse import quote_plus

# MongoDB connection setup
username = quote_plus("rvscret")  # Replace with your MongoDB username
password = quote_plus("Runthistown%401")  # Replace with your MongoDB password
connection_string = f"mongodb+srv://rvscret:Runthistown%401@bankinfo.b85dspa.mongodb.net/"  # Adjust as necessary
client = MongoClient(connection_string)
db = client['bank_info']  # Replace with your database name
collection = db['IFSC_logs']  # Replace with your collection name

# Function to extract PINCODE from the ADDRESS
def extract_pincode(address):
    match = re.search(r'\b\d{6}\b', address)
    if match:
        return match.group(0)
    return ""

# Fetch all documents to update PINCODE field
documents = collection.find()

# Update each document
for doc in documents:
    address = doc.get('ADDRESS', '')
    pincode = extract_pincode(address)
    ifsc = doc.get('IFSC', 'N/A')
    
    # Update the document with the extracted PINCODE
    collection.update_one({'_id': doc['_id']}, {'$set': {'PINCODE': pincode}})
    print(f"Updated document with IFSC: {ifsc} - PINCODE: {pincode}")

print("PINCODE update process completed.")