import os
import time
import requests
import random
import string
import urllib.parse
from dotenv import load_dotenv

# loading environment variables from .env file
load_dotenv()

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_BASE_URL =  "https://api.spotify.com/v1/"

# token caching in order to keep track of current token
token_cache = {
    "access_token": None,
    "refresh_token": None,
    "expires_at": 0
}

# checking if env has all the values we need
def get_spotify_config():
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    redirect_url = os.getenv("SPOTIFY_REDIRECT_URL")

    if not client_id:
        raise RuntimeError("Client id not found")
    
    if not client_secret:
        raise RuntimeError("Client secret id not found")

    if not redirect_url:
        raise RuntimeError("Redirect url not found")
    
    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_url" : redirect_url
    }

# recommended by spotify documentation for security
def generate_random_string(length=16):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))


# requests user authorization and builds the url that the user would login to
def build_user_login_url():
    # Return dictionary of conifguration
    configuration = get_spotify_config()
    state = generate_random_string()
    scope = 'user-read-private user-read-email'

    query_params = {
        'response_type': 'code',
        'client_id': configuration["client_id"],
        'scope': scope,
        'redirect_url': configuration["redirect_url"],
        'state': state
    }

    return 'https://accounts.spotify.com/authorize?' + urllib.parse.urlencode(query_params)

# testing
if __name__ == "__main__":
    configuration = get_spotify_config()
    print(bool(configuration["client_id"]))
    print(bool(configuration["client_secret"]))
    print(bool(configuration["redirect_url"]))

    print()
    login_url = build_user_login_url()
    print(login_url)