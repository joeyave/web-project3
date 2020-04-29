from flask import Flask
from flask_bcrypt import Bcrypt
from flask_session import Session
from flask_socketio import SocketIO
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

bcrypt = Bcrypt()
socketio = SocketIO()
sess = Session()
db = None


def create_app(config):
    app = Flask(__name__)
    app.config.from_object(config)

    bcrypt.init_app(app)
    socketio.init_app(app, ping_interval=20)
    sess.init_app(app)

    global db
    engine = create_engine(app.config['DATABASE_URL'])
    db = scoped_session(sessionmaker(bind=engine))

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
