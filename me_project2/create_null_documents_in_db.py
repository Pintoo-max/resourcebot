import pymongo
from pymongo import MongoClient
import re
from pymongo.operations import UpdateOne
from urllib.parse import quote_plus

# MongoDB connection setup
username = quote_plus("rvscret")  # Replace with your MongoDB username
password = quote_plus("Runthistown%401")  # Replace with your MongoDB password
connection_string = f"mongodb+srv://rvscret:Runthistown%401@bankinfo.b85dspa.mongodb.net/"  # Adjust as necessary
client = MongoClient(connection_string)
db = client['bank_info']  # Replace with your database name
collection = db['IFSC_logs']  # Replace with your collection name

# Update all documents to add the new fields with empty string values
result = collection.update_many(
    {},
    {
        "$set": {
            "FAX": "",
        }
    }
)

# Print the result
print(f'Matched documents: {result.matched_count}')
print(f'Modified documents: {result.modified_count}')