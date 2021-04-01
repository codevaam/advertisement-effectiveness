from flask import Flask
from flask_cors import CORS
import random
import json

app = Flask(__name__)
CORS(app)

from app import views