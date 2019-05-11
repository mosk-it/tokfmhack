from os import environ
import sys
import sqlite3

DATA_DIR = '{}/data'.format(environ['APP_DIR'])

DB_PATH = '{}/data/podcasts.db'.format(environ['APP_DIR'])


def get_app_url():
    if 'APP_URL' in environ:
        return environ['APP_URL']

    return 'http://localhost:5000'

def get_db():
    con = sqlite3.connect(DB_PATH, isolation_level=None)
    con.row_factory=sqlite3.Row
    return con
