import httpx
import time 
from models import Artists

MUSICBRAINZ_URL = "https://musicbrainz.org/ws/2/artist/?query=artist:"

def get_new_artist_info(name: str):
    # Search for the artist using the MusicBrainz API
    time.sleep(1)
    url = MUSICBRAINZ_URL + f'{name}&fmt=json'
    
    new_artist = {"name": name}

    with httpx.Client() as client:
        response = client.get(url)

    if response.status_code == 200:
        data = response.json()
        
        for artist in data:
            if name.lower() == artist["name"].lower():
                new_artist["birthdate"] = artist.get('life-span', {}).get('begin', '') 
            
                birth_location = artist.get('begin-area', {}).get('name', '') 
                birth_country = artist.get('area', {}).get("name", '')
                if birth_country and not birth_location:
                    birth_loc_country = birth_country
                elif birth_location and not birth_country:
                    birth_loc_country = birth_location
                else:
                    birth_loc_country = birth_location + ", " + birth_country
                new_artist['birth_location'] = birth_loc_country
                
                
                ##### 
                ## GET THE COORDS HERE###
                
                
                
                return new_artist
        
        new_artist["birthdate"] = "NOT FOUND IN MUSICBRAINZ"
        new_artist['birth_location'] = "NOT FOUND IN MUSICBRAINZ"
        return new_artist

def fetch_top_artists_info(st_artists: list, mt_artists: list, lt_artists: list):
    # lists of short-term/medium-term/long-term top artist 
    
    all_artist_ids = set().union(
        {artist['id'] for artist in st_artists},
        {artist['id'] for artist in mt_artists},
        {artist['id'] for artist in lt_artists}
    )

    existing_artists = Artists.objects.in_bulk(all_artist_ids, field_name='spotify_id')
    
    all_artist_data = {}
    
    # Loop through each of short-term, medium-term, long-term ID lists
    for artist_list in st_artists, mt_artists, lt_artists:
    
        # Initialize empty list to fill with artist dictionaries 
        list_artist_info = []
        
        # Loop through each artist id in the list 
        for i, id in enumerate(artist_list):
            
            # If artist in existing database, grab relevant info and add to list
            # corresponding to that time period (short-term, medium-term, long-term)
            if id in existing_artists:
                artist = existing_artists[id]
                list_artist_info.append({
                    'rank': i,
                    'spotify_id': artist.spotify_id,
                    'name': artist.name,
                    'birth_latitude': artist.birth_latitude,
                    'birth_longitude': artist.birth_longitude,
                    'birth_date': artist.birth_date,
                    'birth_location': artist.birth_location,
                })    
        else:
            # Placeholder for new artists (to be handled later)
            musicbrainz_info = get_new_artist_info(artist["name"])
              
        
        all_artist_data[artist] = list_artist_info
        
    
    return all_artist_data