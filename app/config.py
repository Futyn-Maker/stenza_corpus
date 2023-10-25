import os

class Config(object):
    SECRET_KEY = os.urandom(32)

DB_NAME = "DoctorWho.db"

POS_TAGS = [
    "ADJ",
    "ADV",
    "INTJ",
    "NOUN",
    "PROPN",
    "VERB",
    "ADP",
    "AUX",
    "CCONJ",
    "DET",
    "NUM",
    "PART",
    "PRON",
    "SCONJ",
    "PUNCT",
    "SYM",
    "X"
]
