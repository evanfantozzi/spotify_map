import httpx
import time 
from .models import Artists
from .coordinates import get_coords
from datetime import datetime

MUSICBRAINZ_URL = "https://musicbrainz.org/ws/2/artist/?query=artist:"

def astrological_sign(birthdate_str: str):
    if is_valid_date(birthdate_str):
        date = datetime.strptime(birthdate_str, "%Y-%m-%d")
        month, day = date.month, date.day

        if (month == 1 and day >= 20) or (month == 2 and day <= 18):
            return "Aquarius"
        elif (month == 2 and day >= 19) or (month == 3 and day <= 20):
            return "Pisces"
        elif (month == 3 and day >= 21) or (month == 4 and day <= 19):
            return "Aries"
        elif (month == 4 and day >= 20) or (month == 5 and day <= 20):
            return "Taurus"
        elif (month == 5 and day >= 21) or (month == 6 and day <= 20):
            return "Gemini"
        elif (month == 6 and day >= 21) or (month == 7 and day <= 22):
            return "Cancer"
        elif (month == 7 and day >= 23) or (month == 8 and day <= 22):
            return "Leo"
        elif (month == 8 and day >= 23) or (month == 9 and day <= 22):
            return "Virgo"
        elif (month == 9 and day >= 23) or (month == 10 and day <= 22):
            return "Libra"
        elif (month == 10 and day >= 23) or (month == 11 and day <= 21):
            return "Scorpio"
        elif (month == 11 and day >= 22) or (month == 12 and day <= 21):
            return "Sagittarius"
        else:  
            return "Capricorn"
    else:
        return None

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
    resp = Artists.objects.create(
        spotify_id = new_artist['spotify_id'],
        name = new_artist['name'], 
        birth_latitude = new_artist.get("birth_latitude"), 
        birth_longitude = new_artist.get("birth_longitude"), 
        birth_date = new_artist.get("birth_date"),
        birth_location = new_artist.get("birth_location"), 
        complete_artist_json = new_artist.get("spotify_info")
    )

def get_new_artist_info(name: str):
    # Search for the artist using the MusicBrainz API
    time.sleep(1)
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

def fetch_artists_info(st_artists: list, mt_artists: list, lt_artists: list) -> dict:
    # Lists of short-term/medium-term/long-term top artist IDs 
    all_artist_ids = set().union(
        {artist['spotify_id'] for artist in st_artists},
        {artist['spotify_id'] for artist in mt_artists},
        {artist['spotify_id'] for artist in lt_artists}
    )

    # Existing artists in database that match that 
    existing_artists = Artists.objects.in_bulk(all_artist_ids, field_name='spotify_id')
    
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
                if existing_artist.birth_date:
                    sign = astrological_sign(existing_artist.birth_date.isoformat())
                artist_dictionaries.append({
                    'rank': i+1,
                    'spotify_id': artist['spotify_id'],
                    'name': artist['name'],
                    'birth_latitude': existing_artist.birth_latitude,
                    'birth_longitude': existing_artist.birth_longitude,
                    'birth_date': existing_artist.birth_date.isoformat() if existing_artist.birth_date else None,
                    'birth_location': existing_artist.birth_location,
                    'photo': existing_artist.complete_artist_json["images"][0]["url"] if existing_artist.complete_artist_json.get("images") else None,
                    'sign': sign
                })    
            else:
                # Search for new artist dictionary 
                new_artist = get_new_artist_info(artist["name"])
                
                # If new artist found in MusicBrainz:
                if new_artist:
                    
                    # Add to list of short-term/medium-term/long-term artists
                    new_artist["rank"] = i+1
                    new_artist["spotify_id"] = artist["spotify_id"]
                    new_artist["sign"] = astrological_sign(new_artist.get("birth_date",""))
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