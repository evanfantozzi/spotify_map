import spotipy
from spotipy.oauth2 import SpotifyOAuth
from django.conf import settings
from spotify_map.models import Artists

# Spotify OAuth setup
sp_oauth = SpotifyOAuth(
    client_id=settings.SPOTIPY_CLIENT_ID,
    client_secret=settings.SPOTIPY_CLIENT_SECRET,
    redirect_uri=settings.SPOTIPY_REDIRECT_URI,
    scope="user-top-read"  # Scope for fetching top artists
)

def get_spotify_client(token_info):
    """
    Returns a Spotipy client instance.
    """
    return spotipy.Spotify(auth=token_info['access_token'])

def fetch_top_spotify_artists(sp, time_range="long_term"):
    """
    Fetch the Spotify IDs of the user's top artists for a specific time range.

    Args:
        sp: Spotify client instance.
        time_range: One of 'long_term', 'medium_term', or 'short_term'.
        limit: Number of artists to fetch (default is 50).

    Returns:
        List of Spotify IDs of top artists.
    """
    if time_range not in {"long_term", "medium_term", "short_term"}:
        raise ValueError(f"Invalid time_range: {time_range}. Choose 'long_term', 'medium_term', or 'short_term'.")

    # Request top artists from Spotify
    results = sp.current_user_top_artists(time_range=time_range, limit=50)
    
    # Rename id key to spotify_id
    for artist in results["items"]:
        artist["spotify_id"] = artist.pop("id")
    
    # Return them
    return results["items"]

def get_authorize_url():
    """
    Returns the authorization URL for logging in to Spotify.
    """
    return sp_oauth.get_authorize_url()

def get_access_token(code):
    """
    Get the access token from Spotify using the authorization code.
    
    Args:
        code: The authorization code returned by Spotify.
    
    Returns:
        Token information including access token, refresh token, etc.
    """
    return sp_oauth.get_access_token(code)

def refresh_access_token(refresh_token):
    """
    Refresh the access token using the refresh token.
    
    Args:
        refresh_token: The refresh token previously obtained.
    
    Returns:
        New access token information.
    """
    return sp_oauth.refresh_access_token(refresh_token)
