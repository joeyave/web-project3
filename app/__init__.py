import os

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_session import Session
from flask_socketio import SocketIO
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)
app.config.from_object(os.environ.get('FLASK_ENV') or 'config.DevelopmentConfig')

bcrypt = Bcrypt(app)
socketio = SocketIO(app, ping_interval=20)
Session(app)

# Set up database
engine = create_engine(app.config['DATABASE_URL'])
db = scoped_session(sessionmaker(bind=engine))

from . import views
