from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL

import os
from dotenv import load_dotenv
load_dotenv()

DRIVERNAME = os.getenv("DRIVERNAME")
USERNAME = os.getenv("USERNAMEDB")
PASSWORD = os.getenv("PASSWORD")
HOST = os.getenv("HOST")
PORT = os.getenv("PORT")
DATABASE = os.getenv("DATABASE")
SCHEMA = os.getenv("SCHEMA")

def run():
    engine = create_engine(
        URL.create(
            DRIVERNAME, USERNAME, PASSWORD, HOST, PORT, DATABASE
        ),connect_args={'options': '-csearch_path={}'.format(SCHEMA)}
    )

    return engine