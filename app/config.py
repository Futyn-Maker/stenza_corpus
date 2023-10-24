import os

class Config(object):
    SECRET_KEY = os.urandom(32)

DB_NAME = "DoctorWho.db"
