import os
from dotenv import load_dotenv

load_dotenv()

SQLALCHEMY_DATABASE_URL = "postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}".format(
    DB_HOST=os.getenv("POSTGRES_HOST"),
    DB_PORT=os.getenv("POSTGRES_PORT"),
    DB_NAME=os.getenv("POSTGRES_DB"),
    DB_USER=os.getenv("POSTGRES_USER"),
    DB_PASSWORD=os.getenv("POSTGRES_PASSWORD")
)

SECRET_KEY = os.getenv("SECRET_KEY")
