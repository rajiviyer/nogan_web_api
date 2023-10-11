from flask import Flask
import os

app = Flask(__name__)

# Configuration variable
app.config['RESULT_DIR'] = os.path.join(os.getcwd(),"app/data")
app.config['STRETCH_TYPE'] = set(["Uniform","Gaussian"])

from app import views