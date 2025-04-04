from geopy.geocoders import Nominatim
from time import sleep
from .models import Coordinates
import re

def store_coordinates_in_db(location: str, lat: float, lon: float):
    resp = Coordinates.objects.create(location=location, latitude=lat, longitude=lon)
    if not resp:
        print(f"Error adding {location} to coordinates database - skipping doing so")

def get_coords(location: str) -> tuple[float, float] | None:
    geolocator = Nominatim(user_agent="Spotify_Apps") 
    
    # Look to see if location already in coordinates database
    db_coordinates = Coordinates.objects.filter(location = location).first()
    
    # If location already in dataset, return those coordinates
    if db_coordinates:
        return (db_coordinates.latitude, db_coordinates.longitude)  
    
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
                
                if len(location_parts > 1):
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
            
           
