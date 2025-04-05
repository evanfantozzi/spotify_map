import os
import psycopg2
from geopy.geocoders import Nominatim
from time import sleep
from dotenv import load_dotenv


# Load environment variables from .env
load_dotenv()

# Fetching environment variables for the database connection
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')

connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Initialize Geolocator
geolocator = Nominatim(user_agent="spotify_map_coordinates")

def clear_coordinates_db():
    """ Clears the coordinates table to start fresh """
    connection = psycopg2.connect(connection_string)
    cursor = connection.cursor()
    try:
        delete_query = "DELETE FROM spotify_map_coordinates;"
        cursor.execute(delete_query)
        connection.commit()
        print("Successfully cleared coordinates database.")
    except Exception as e:
        print(f"Error clearing coordinates database: {e}")
    finally:
        cursor.close()
        connection.close()

def check_location_exists(location: str):
    """ Check if the location already exists in the coordinates database """
    connection = psycopg2.connect(connection_string)
    cursor = connection.cursor()
    try:
        select_query = "SELECT * FROM spotify_map_coordinates WHERE location = %s LIMIT 1;"
        cursor.execute(select_query, (location,))
        db_coordinates = cursor.fetchone()
        
        if db_coordinates:
            print(f"Location {location} found in database.")
            return db_coordinates
        else:
            print(f"Location {location} not found in database.")
            return None
    except Exception as e:
        print(f"Error checking if location exists: {e}")
        return None
    finally:
        cursor.close()

def store_coordinates_in_db(location: str, lat: float, lon: float):
    """ Store the coordinates of the location in the database """
    connection = psycopg2.connect(connection_string)
    cursor = connection.cursor()
    try:
        insert_query = """
        INSERT INTO spotify_map_coordinates (location, latitude, longitude)
        VALUES (%s, %s, %s);
        """
        cursor.execute(insert_query, (location, lat, lon))
        connection.commit()
        print(f"   Successfully added {location} to coordinates database.")
    except Exception as e:
        print(f"   Error adding {location} to coordinates database: {e}")
    finally:
        cursor.close()

def get_coordinates_from_location(location: str):
    """ Fetch the coordinates for a location using Geopy """
    try:
        sleep(1.2)
        location_data = geolocator.geocode(location)
        if location_data:
            return location_data.latitude, location_data.longitude
        else:
            print(f"Could not find coordinates for {location}")
            return None, None
    except Exception as e:
        print(f"Error fetching coordinates for {location}: {e}")
        return None, None

def get_artists_from_db():
    """ Fetch artists from the spotify_map_artists database """
    connection = psycopg2.connect(connection_string)
    cursor = connection.cursor()
    try:
        select_query = """
        SELECT spotify_id, name, birth_location FROM spotify_map_artists;
        """
        cursor.execute(select_query)
        artists = cursor.fetchall()
        artist_list = [{'spotify_id': artist[0], 'name': artist[1], 'birth_location': artist[2]} for artist in artists]
        return artist_list
    except Exception as e:
        print(f"Error fetching artists from database: {e}")
        return []
    finally:
        cursor.close()

def process_artists_and_store_coordinates():
    """ Process each artist, check their location, fetch coordinates, and store them in the database """
    artists = get_artists_from_db()
    
    for artist in artists:
        location = artist.get('birth_location')  # Get the artist's birth location

        if location:
            # Check if the location exists in the coordinates database
            if not check_location_exists(location):
                lat, lon = get_coordinates_from_location(location)
                
                if lat and lon:
                    # Store the coordinates in the database
                    store_coordinates_in_db(location, lat, lon)

# Clear the existing coordinates from the database

# Process the artists and store coordinates
process_artists_and_store_coordinates()
