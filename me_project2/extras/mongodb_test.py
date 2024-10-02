
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

# import settings
# import database

app = FastAPI()
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://rvscret:Runthistown%401@bankinfo.b85dspa.mongodb.net/?retryWrites=true&w=majority&appName=bankinfo"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)