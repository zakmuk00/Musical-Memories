import os
import time
import requests
import random
import string
import urllib.parse
from dotenv import load_dotenv

# loading environment variables from .env file
load_dotenv()


class SpotifyClient:
    def __init__(self):
        # initialize urls
        self.auth_url = "https://accounts.spotify.com/authorize"
        self.token_url = "https://accounts.spotify.com/api/token"
        self.base_url = "https://api.spotify.com/v1/"

        # initialize env variables
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        self.redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")

        # initialize tokens
        self.access_token = None
        self.refresh_token = None
        self.expires_at = 0

        # checks to see if env file has the necessasry values
        if not self.client_id:
            raise RuntimeError("Client id not found")
    
        if not self.client_secret:
            raise RuntimeError("Client secret id not found")

        if not self.redirect_uri:
            raise RuntimeError("Redirect uri not found")

        # parameters for generating random string
        self.length = 16
        self.characters = string.ascii_letters + string.digits

    # recommended by spotify documentation for security
    def generate_random_string(self):
        return ''.join(random.choices(self.characters, k=self.length))


    # requests user authorization and builds the url that the user would login to
    def build_user_login_url(self):
        state = self.generate_random_string()
        scope = 'user-read-private user-read-email'

        query_params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'scope': scope,
            'redirect_uri': self.redirect_uri,
            'state': state,
            'show_dialog' : 'false'
        }

        return f"{self.auth_url}?{urllib.parse.urlencode(query_params)}"

# testing
if __name__ == "__main__":
    spotify = SpotifyClient()

    login_url = spotify.build_user_login_url()
    print(login_url)