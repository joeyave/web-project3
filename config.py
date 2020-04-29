import os

app_dir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig:
    SECRET_KEY = os.getenv('SECRET_KEY') or 'secret key'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.getcwd() + '/app/static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    SESSION_PERMANENT = False
    SESSION_TYPE = "filesystem"


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    DATABASE_URL = os.getenv("DATABASE_URL") or \
                   'postgres://cwvpjbiwlknvyn:eb091840c5b7277fbcc5b0f153d1504aa2b1b749a3199fce48df94adf5081aff@ec2-54-86-170-8.compute-1.amazonaws.com:5432/d9em3ulua14l5n'


class TestingConfig(BaseConfig):
    DEBUG = True
    DATABASE_URL = os.getenv("DATABASE_URL") or \
                   'postgres://cwvpjbiwlknvyn:eb091840c5b7277fbcc5b0f153d1504aa2b1b749a3199fce48df94adf5081aff@ec2-54-86-170-8.compute-1.amazonaws.com:5432/d9em3ulua14l5n'


class ProductionConfig(BaseConfig):
    DEBUG = False
    DATABASE_URL = os.getenv("DATABASE_URL") or \
                   'postgres://cwvpjbiwlknvyn:eb091840c5b7277fbcc5b0f153d1504aa2b1b749a3199fce48df94adf5081aff@ec2-54-86-170-8.compute-1.amazonaws.com:5432/d9em3ulua14l5n'
