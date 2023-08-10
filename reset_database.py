import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

db_config = {
    "dbname": os.environ.get("POSTGRES_DB", "ou_db"),
    "user": os.environ.get("POSTGRES_USER", "postgres"),
    "password": os.environ.get("POSTGRES_PASSWORD", "postgres"),
    "host": os.environ.get("POSTGRES_HOST", "127.0.0.1"),
    "port": os.environ.get("POSTGRES_PORT", "5432"),
}


def create_database():
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user=db_config["user"],
            password=db_config["password"],
            host=db_config["host"],
            port=db_config["port"],
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Drop the existing database if it exists
        cursor.execute(f"DROP DATABASE IF EXISTS {db_config['dbname']}")

        # Create a new database
        cursor.execute(f"CREATE DATABASE {db_config['dbname']}")

        cursor.close()
        conn.close()

        print("Database dropped and recreated successfully!")

    except Exception as e:
        print("An error occurred:", e)


if __name__ == "__main__":
    create_database()
