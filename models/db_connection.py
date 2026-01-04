#fonction de connection de la bdd
import psycopg2
from models.db_config import DB_CONFIG

def get_connection():
    return psycopg2.connect(**DB_CONFIG)