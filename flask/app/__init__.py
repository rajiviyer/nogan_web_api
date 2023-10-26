from flask import Flask
from flask_socketio import SocketIO
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Configuration variable
app.config['RESULT_DIR'] = os.path.join(os.getcwd(),"app/data")
app.config['SEED_DATA_DIR'] = \
                    os.path.join(os.getcwd(),"app/seed_data")
app.config['STRETCH_TYPE'] = set(["Uniform","Gaussian"])
app.config['NA_VALUES_LIST'] = [' ', 'NA', 'NaN', 'N/A']

from app import views

if __name__ == '__main__':
    socketio.run(app)