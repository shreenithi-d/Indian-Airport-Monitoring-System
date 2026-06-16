import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "database",
    "airport.db"
)

SECRET_KEY = "airport_monitoring_secret_key_2026"