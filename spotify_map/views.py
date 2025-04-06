from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout
from .musicbrainz import fetch_artists_info
from .spotify_utils import get_authorize_url, get_access_token, fetch_top_spotify_artists, get_spotify_client
from django.conf import settings
from django.http import HttpResponseRedirect
from django.core.cache import cache
from django.http import JsonResponse
import time

# --- Landing Route (Pre-login) ---
def landing(request):
    """
    Landing page shown before the user logs in.
    Clears session tokens or any user-related data if they are already logged in.
    """
    # Clear session data if the user is already logged in and visiting the landing page
    request.session.flush()  # Clear all session data

    if 'token_info' in request.session:
        del request.session['token_info']  # If token exists, delete it manually

    if 'artists' in request.session:
        del request.session['artists']  # If artists data exists, delete it manually

    return render(request, 'landing.html')

# --- Home Route (Post-login) ---
def home(request):
    """
    Home page shown after the user logs in.
    Displays top artists for different time ranges (short, medium, long term).
    """
    if 'artists' not in request.session:
        return redirect('login')  # Redirect to login if no artists are available

    # Get the full artist data (the dictionary of 3 lists: st_artists, mt_artists, lt_artists)
    artists_data = request.session.get('artists', None)

    return render(request, 'home.html', {'artists_data': artists_data})

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
    Callback page: Get access token and store it in the session.
    """
    code = request.GET.get('code')  # Spotify's code returned after successful login
    token_info = get_access_token(code)  # Get access token using the code
    request.session['token_info'] = token_info  # Store token info in session

    # Redirect to loading_page to start fetching data and render loading page
    return redirect('loading_page')


def loading_page(request):
    """
    Renders the loading screen. JS will poll `start_loading`.
    """
    return render(request, 'loading.html')

def start_loading(request):
    """
    Actually loads artist data and returns a status update.
    """
    token_info = request.session.get('token_info', None)
    if not token_info:
        return JsonResponse({'error': 'No token'}, status=403)

    sp = get_spotify_client(token_info)

    # Fetch artist data
    st_artists = fetch_top_spotify_artists(sp, "short_term")
    mt_artists = fetch_top_spotify_artists(sp, "medium_term")
    lt_artists = fetch_top_spotify_artists(sp, "long_term")
    all_artists = fetch_artists_info(st_artists, mt_artists, lt_artists)

    # Store in session
    request.session['artists'] = all_artists
    request.session['loading_complete'] = True
    request.session.modified = True

    return JsonResponse({'success': True})

def check_loading_status(request):
    """
    Checks if the artist loading process is complete.
    Returns a JSON response with the loading status.
    """
    loading_complete = request.session.get('loading_complete', False)
    return JsonResponse({'loading_complete': loading_complete})

def top_artists(request, time_range):
    """
    Displays top artists for a specific time range.
    """
    if 'artists' not in request.session:
        return redirect('login')  # Redirect to login if no artists are available

    # Get the artist data for the requested time range
    artists_data = request.session.get('artists', None)

    if time_range == 'short':
        artists = artists_data.get('st_artists', [])
    elif time_range == 'medium':
        artists = artists_data.get('mt_artists', [])
    elif time_range == 'long':
        artists = artists_data.get('lt_artists', [])
    else:
        # Handle invalid time range
        return redirect('home')  # Redirect to home if the time_range is invalid
    return render(request, 'top_artists.html', {'artists': artists, 'time_range': time_range})

# --- Logout Route ---
def logout(request):
    """
    Logs out the user from Django, then shows a page that forces them to log out from Spotify.
    """
    # Log the user out from Django
    cache.clear()
    auth_logout(request)
    request.session.flush()  # Clear session data


    # Redirect to a custom page that will handle Spotify logout and return to our site
    return redirect('logout_redirect')

def logout_redirect(request):
    """
    Renders a page that opens the Spotify logout and then redirects back.
    """
    return render(request, 'logout_redirect.html')