import os
import time
import requests
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

# testing
if __name__ == "__main__":
    configuration = get_spotify_config()
    print(bool(configuration["client_id"]))
    print(bool(configuration["client_secret"]))
    print(bool(configuration["redirect_url"]))