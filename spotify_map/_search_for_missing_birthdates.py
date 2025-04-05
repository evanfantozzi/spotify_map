import psycopg2
import os
import csv
from dotenv import load_dotenv
import httpx

# Load environment variables from .env
load_dotenv()

# Fetching environment variables for the database connection
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')

# Create the connection string
connection_string = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Connect to your PostgreSQL database
connection = psycopg2.connect(connection_string)
cursor = connection.cursor()

# Query to get artists with missing birth_date
cursor.execute("SELECT spotify_id, name FROM spotify_map_artists WHERE birth_date IS NULL")

# Fetch the results
artists_missing_birth_date = cursor.fetchall()

# Function to fetch artist birthday from Wikidata
def get_artist_birthday(artist):
    query = f"""
    SELECT ?birthdate WHERE {{
      ?person rdfs:label "{artist}"@en;
              wdt:P569 ?birthdate.
    }} LIMIT 1
    """
    url = "https://query.wikidata.org/sparql"
    headers = {"User-Agent": "ArtistBirthdayFetcher/1.0"}
    params = {"query": query, "format": "json"}

    try:
        response = httpx.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        results = response.json().get("results", {}).get("bindings", [])
        if results:
            return results[0]["birthdate"]["value"]
        return "Birthday not found"
    except Exception as e:
        return f"Error: {str(e)}"

# Loop through artists with missing birthdates
for artist in artists_missing_birth_date:
    spotify_id, name = artist
    print(f"Fetching birthday for {name}...")

    # Get birthday from Wikidata
    birthday = get_artist_birthday(name)
    print(f"{name}: {birthday}")

    # Optionally, update the database with the fetched birthday
    '''
    if birthday != "Birthday not found":
        cursor.execute("""
            UPDATE spotify_map_artists
            SET birth_date = %s
            WHERE spotify_id = %s
        """, (birthday, spotify_id))
        connection.commit()
'''
# Close the cursor and connection
cursor.close()
connection.close()

# Output to CSV file (if needed)
csv_file_path = 'artists_missing_birth_date.csv'

with open(csv_file_path, mode='w', newline='') as file:
    writer = csv.writer(file)
    
    # Write the header
    writer.writerow(['Spotify ID', 'Name'])
    
    # Write the query results
    writer.writerows(artists_missing_birth_date)

print(f"Results have been written to {csv_file_path}")
