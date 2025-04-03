from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from .spotify_utils import get_authorize_url, get_access_token, fetch_top_spotify_artists, get_spotify_client
from musicbrainz import fetch_top_artists_info

# --- Landing Route (Pre-login) ---
def landing(request):
    """
    Landing page shown before the user logs in.
    Provides an option to log in to Spotify.
    """
    # If the user is already logged in, redirect to the home page
    if 'token_info' in request.session:
        return redirect('home')
    
    return render(request, 'landing.html')

# --- Home Route (Post-login) ---
def home(request):
    """
    Home page shown after the user logs in.
    Allows the user to view their top artists and select a time range.
    """
    if 'token_info' not in request.session:
        return redirect('login')  # Redirect to login if not logged in

    artists = request.session.get('artists', None)
    
    if not artists:
        return redirect('login_callback')  # Redirect to fetch top artists if they're not available in session

    return render(request, 'home.html', {'artists': artists})

# --- Login Route to redirect user to Spotify authorization ---
def login(request):
    """
    Redirects the user to Spotify authorization page.
    """
    auth_url = get_authorize_url()  # Get the Spotify authorization URL
    return redirect(auth_url)

# --- Callback from Spotify after user logs in ---
def login_callback(request):
    """
    Callback page: get access token and fetch top artists.
    """
    code = request.GET.get('code')  # Spotify's code returned after successful login
    token_info = get_access_token(code)  # Get access token using the code
    request.session['token_info'] = token_info  # Store token info in session
    
    # Get Spotify client with the access token
    sp = get_spotify_client(token_info)
    
    # Fetch top artists (default is long_term)
    st_artists = fetch_top_spotify_artists(sp, "short_term")
    mt_artists = fetch_top_spotify_artists(sp, "medium_term")
    lt_artists = fetch_top_spotify_artists(sp, "long_term")
    
    all_artists = fetch_top_artists_info(st_artists, mt_artists, lt_artists)
    
    
    # Get list of unique artist IDs
   
    
    
    
    # Store the artists in the session
    request.session['artists'] = artists
    
    return redirect('home')  # Redirect to home after fetching artists

# ---
