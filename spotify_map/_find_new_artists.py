import os
import requests
from dotenv import load_dotenv
import httpx
from time import sleep
from datetime import datetime
import psycopg2
from geopy.geocoders import Nominatim
import json
import httpx
from lxml import html



# Load environment variables from .env
load_dotenv()

# Fetching environment variables for the database connection
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

# Spotify API URL for token
TOKEN_URL = "https://accounts.spotify.com/api/token"

connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def store_coordinates_in_db(location: str, lat: float, lon: float):
    # Create the connection string
    connection = psycopg2.connect(connection_string)
    cursor = connection.cursor()
    try:
        # Prepare the SQL insert query
        insert_query = """
        INSERT INTO spotify_map_coordinates (location, latitude, longitude)
        VALUES (%s, %s, %s);
        """
        
        # Execute the query with the provided values
        cursor.execute(insert_query, (location, lat, lon))
        
        # Commit the transaction
        connection.commit()
        
        print(f"Successfully added {location} to coordinates database.")
    
    except Exception as e:
        print(f"Error adding {location} to coordinates database: {e}")
    
    finally:
        # Close the cursor and connection if needed
        cursor.close()


def check_location_exists(location: str):
    connection = psycopg2.connect(connection_string)
    cursor = connection.cursor()
    try:
        # Prepare the SQL query to check if the location exists
        select_query = """
        SELECT * FROM spotify_map_coordinates WHERE location = %s LIMIT 1;
        """
        
        # Execute the query
        cursor.execute(select_query, (location,))
        
        # Fetch the first result
        db_coordinates = cursor.fetchone()
        
        # If db_coordinates is None, no location was found
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
        # Close the cursor if necessary (optional depending on your needs)
        cursor.close()


def get_coords(location: str) -> tuple[float, float] | None:
    geolocator = Nominatim(user_agent="Spotify_Apps") 
    
    # Look to see if location already in coordinates database
    db_coordinates = check_location_exists(location)
    
    # If location already in dataset, return those coordinates
    if db_coordinates:
        return (db_coordinates[0], db_coordinates[1])  
    
    else:    
         # Attempt to search for location coordinates
            sleep(1.1)
            coords = geolocator.geocode(location)
            if coords:
                # Coordinates found, returning those
                store_coordinates_in_db(location, coords.latitude, coords.longitude)
                return (coords.latitude, coords.longitude)
            
            else:
                # Initial search didn't work. Try searching on location country 
                location_parts = location.split(",")
                
                if len(location_parts) > 1:
                    # Format is [city, country] or [city, state, country], etc.
                    sleep(1.1)
                    coords = geolocator.geocode(location_parts[-1])
                    if coords:
                        # Coordinates found for country, returning those 
                        store_coordinates_in_db(location, coords.latitude, coords.longitude)
                        return (coords.latitude, coords.longitude)
                    else:
                        # Country coordinates not found, unsuccessful search         
                        return None
                    
                else:
                    # Nothing else to search for, unsuccessful search 
                    return None


MUSICBRAINZ_URL = "https://musicbrainz.org/ws/2/artist/?query=artist:"

def is_valid_date(date_string):
    """
    Checks if a string is a valid date in the format mm-dd-yyyy.

    Args:
        date_string: The string to check.

    Returns:
        True if the string is a valid date, False otherwise.
    """
    format_string = "%Y-%m-%d"
    try:
        datetime.strptime(date_string, format_string)
        return True
    except ValueError:
        return False


def store_artist_in_db(new_artist: dict):
    # Connect to your PostgreSQL database
    connection = psycopg2.connect(connection_string)
    cursor = connection.cursor()
    try:
        # Prepare the SQL query to insert the new artist
        insert_query = """
        INSERT INTO spotify_map_artists (
            spotify_id, 
            name, 
            birth_latitude, 
            birth_longitude, 
            birth_date, 
            birth_location, 
            complete_artist_json
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        
        # Execute the query with the new artist data
        cursor.execute(insert_query, (
            new_artist['spotify_id'], 
            new_artist['name'], 
            new_artist.get("birth_latitude"), 
            new_artist.get("birth_longitude"), 
            new_artist.get("birth_date"), 
            new_artist.get("birth_location"), 
            json.dumps(new_artist.get("spotify_info", {}))
        ))
        
        # Commit the transaction
        connection.commit()
        
        print(f"Successfully added artist {new_artist['name']} to the database.")
    
    except Exception as e:
        print(f"Error adding artist {new_artist['name']} to the database: {e}")
    
    finally:
        # Close the cursor if needed
        cursor.close()
        

def get_new_artist_info(name: str):
    # Search for the artist using the MusicBrainz API
    sleep(1)
    url = MUSICBRAINZ_URL + f'{name}&fmt=json'
    
    new_artist = {"name": name}

    with httpx.Client() as client:
        response = client.get(url)

    if response.status_code == 200:
        data = response.json()
        
        for artist in data["artists"]:
            if name.lower() == artist["name"].lower():
                
                # Get birthdate 
                birthdate = artist.get('life-span', {}).get('begin', '')
                if is_valid_date(birthdate):
                    new_artist["birth_date"] = birthdate.isoformat()
                
                
                # Get birth location
                birth_city = artist.get('begin-area', {}).get('name', '') 
                birth_country = artist.get('area', {}).get("name", '')
                
                if birth_country or birth_city:
                    if birth_country and birth_city:
                        birth_location = birth_city + ", " + birth_country
                    elif birth_country and not birth_city:
                        birth_location = birth_country
                    elif birth_city and not birth_country:
                        birth_location = birth_city
                    
                    new_artist['birth_location'] = birth_location
                
                    # Get birth lat/lon 
                    coords = get_coords(birth_location)
                    if coords:
                        new_artist['birth_latitude'] = coords[0]
                        new_artist['birth_longitude'] = coords[1]
                        
                # Store Musicbrainz data 
                new_artist["musicbrainz_data"] = artist
                return new_artist
    
    # No artist found
    print(f"Artist {name} not found in Musicbrainz")
    return None


def get_existing_artists(all_artist_ids):
    connection = psycopg2.connect(connection_string)
    cursor = connection.cursor()

    try:
        # Convert set to a list
        all_artist_ids = list(all_artist_ids)
        
        select_query = """
        SELECT * FROM spotify_map_artists WHERE spotify_id = ANY(%s);
        """
        cursor.execute(select_query, (all_artist_ids,))
        existing_artists = cursor.fetchall()
        
        # Convert list of tuples to a dictionary
        artist_dict = {artist[0]: artist for artist in existing_artists}  # Assuming spotify_id is the first element
        
        return artist_dict
    
    except Exception as e:
        print(f"Error fetching existing artists: {e}")
        return {}
    
    finally:
        cursor.close()
    



def fetch_artists_info(st_artists: list, mt_artists: list, lt_artists: list) -> dict:
    # Lists of short-term/medium-term/long-term top artist IDs 
    all_artist_ids = set().union(
        {artist['spotify_id'] for artist in st_artists},
        {artist['spotify_id'] for artist in mt_artists},
        {artist['spotify_id'] for artist in lt_artists}
    )

    # Existing artists in database that match that 
    existing_artists = get_existing_artists(all_artist_ids)
    
    all_artist_data = {}
    
    # Loop through each of short-term, medium-term, long-term ID lists
    for list_i, top_artist_list in enumerate([st_artists, mt_artists, lt_artists]):
    
        # Initialize empty list to fill with artist dictionaries 
        artist_dictionaries = []
        
        # Loop through each of the user's top artists
        for i, artist in enumerate(top_artist_list):
            
            # If artist in existing database, grab relevant info and add to list
            # corresponding to that time period (short-term, medium-term, long-term)
            if artist['spotify_id'] in existing_artists:
                existing_artist = existing_artists[artist['spotify_id']]
                artist_dictionaries.append({
        'rank': i + 1,
        'spotify_id': artist['spotify_id'],
        'name': artist['name'],
        'birth_latitude': existing_artist[2],  # Index 2 is the latitude
        'birth_longitude': existing_artist[3],  # Index 3 is the longitude
        'birth_date': existing_artist[4].isoformat() if existing_artist[4] else None,  # Index 4 is the birth_date
        'birth_location': existing_artist[5],  # Index 5 is the birth_location
        'photo': existing_artist[6]["images"][0]["url"] if existing_artist[6].get("images") else None  # Index 6 is the complete_artist_json
    })   
            else:
                # Search for new artist dictionary 
                new_artist = get_new_artist_info(artist["name"])
                
                # If new artist found in MusicBrainz:
                if new_artist:
                    
                    # Add to list of short-term/medium-term/long-term artists
                    new_artist["rank"] = i+1
                    new_artist["spotify_id"] = artist["spotify_id"]
                    del new_artist["musicbrainz_data"] # for now, not including 
                    artist_dictionaries.append(new_artist)
                                        
                    # Store in artist database 
                    new_artist["spotify_info"] = artist
                    store_artist_in_db(new_artist)

                # New artist not found in MusicBrainz
                else:
                    # Only append the information we have from Spotify
                    artist_dictionaries.append({
                        'rank': i+1,
                        'spotify_id': artist['spotify_id'],
                        'name': artist['name'],
                    })
            
        # Add list of short-term/medium-term/long-term artist dictionaries to 
        # the all artist data dictionary
        if list_i == 0:
            all_artist_data["st_artists"] = artist_dictionaries
        elif list_i == 1:
            all_artist_data["mt_artists"] = artist_dictionaries
        elif list_i == 2:
            all_artist_data["lt_artists"] = artist_dictionaries
    
    # Return dictionary of 3 lists of dictionaries
    return all_artist_data

# Function to authenticate and get the access token
def get_access_token():
    auth_response = requests.post(TOKEN_URL, {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    })
    auth_response_data = auth_response.json()
    return auth_response_data['access_token']

# Function to search for an artist by name and grab their info
def search(artist_name):
    access_token = get_access_token()

    # Spotify API endpoint for searching an artist
    SEARCH_URL = f"https://api.spotify.com/v1/search?q={artist_name}&type=artist&limit=1"

    # Headers with the access token for authorization
    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    # Send request to search for the artist
    response = requests.get(SEARCH_URL, headers=headers)
    data = response.json()

    if 'artists' in data and data['artists']['items']:
        artist = data['artists']['items'][0]
        artist["spotify_id"] = artist.pop("id")
        fetch_artists_info([artist], [], [])


url = f"https://kworb.net/itunes/extended.html"
response = httpx.get(url)

if response.status_code == 200:
    tree = html.fromstring(response.text)
    artist_rows = tree.xpath('//tr')  # Find all the rows in the table
    for artist in artist_rows:
        name = artist.xpath('.//a/text()')
        print(name)
        search(name)


