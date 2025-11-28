import os
import string


MAX_SHORT_ID_LENGTH = 16
ALLOWED_CHARS = string.ascii_letters + string.digits
SHORT_ID_LENGTH = 6


class Config(object):
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI')
    SECRET_KEY = os.getenv('SECRET_KEY')
    DISK_TOKEN = os.getenv('DISK_TOKEN')
