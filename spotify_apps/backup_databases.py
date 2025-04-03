import os
import subprocess
from dotenv import load_dotenv
import psycopg2
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# Get PostgreSQL credentials from environment variables
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# Connect to PostgreSQL
connection = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)


def back_up_artists():
    cur = connection.cursor() 
    
# Get columns for the 'artists' table
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'spotify_map_artists';
    """)
    columns = cur.fetchall()
    print("Columns in the 'artists' table:")
    for column in columns:
        print(f"{column[0]} - {column[1]}")

    # Fetch data from the 'artists' table
    cur.execute("SELECT name, birth_location, birth_date FROM spotify_map_artists LIMIT 10;")  # Fetch first 10 rows
    rows = cur.fetchall()
    print("\nFirst 10 rows of the 'artists' table:")
    for row in rows:
        print(row)

    # Backup the PostgreSQL database schema and data to a .sql file using pg_dump
    backup_file = Path(__file__).parent / "data" / "backup_artist_db.sql"

    # Use the full path to pg_dump
    pg_dump_command = [
        "/opt/homebrew/bin/pg_dump",  # Full path to pg_dump
        "-U", DB_USER,
        "-d", DB_NAME,
        "--table=spotify_map_artists",
        "--file", str(backup_file)
    ]

    # Use subprocess to execute the pg_dump command
    try:
        subprocess.run(pg_dump_command, check=True, env={"PGPASSWORD": DB_PASSWORD})
        print(f"\nDatabase (schema and data) has been backed up to {backup_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while creating backup: {e}")
        # Close the cursor and connection
    cur.close()
    connection.close()

def back_up_coords():
    cur = connection.cursor() 
    
# Get columns for the 'artists' table
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'spotify_map_coordinates';
    """)
    columns = cur.fetchall()
    print("Columns in the 'coords' table:")
    for column in columns:
        print(f"{column[0]} - {column[1]}")

    # Fetch data from the 'artists' table
    cur.execute("SELECT id, location, longitude, latitude FROM spotify_map_coordinates LIMIT 10;")  # Fetch first 10 rows
    rows = cur.fetchall()
    print("\nFirst 10 rows of the 'coords' table:")
    for row in rows:
        print(row)

    # Backup the PostgreSQL database schema and data to a .sql file using pg_dump
    backup_file = Path(__file__).parent / "data" / "backup_coords_db.sql"

    # Use the full path to pg_dump
    pg_dump_command = [
        "/opt/homebrew/bin/pg_dump",  # Full path to pg_dump
        "-U", DB_USER,
        "-d", DB_NAME,
        "--table=spotify_map_coordinates",
        "--file", str(backup_file)
    ]

    # Use subprocess to execute the pg_dump command
    try:
        subprocess.run(pg_dump_command, check=True, env={"PGPASSWORD": DB_PASSWORD})
        print(f"\nDatabase (schema and data) has been backed up to {backup_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while creating backup: {e}")
        # Close the cursor and connection
    cur.close()
    

back_up_coords()
back_up_artists()
connection.close()