import os

from app import socketio, create_app

app = create_app(os.getenv('FLASK_ENV') or 'config.DevelopmentConfig')

if __name__ == '__main__':
    socketio.run(app)
