import os
import time
import requests
import random
import string
import urllib.parse
import base64
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

    # header needed for Spotify's token endpoint
    def get_auth_header(self):
        auth_string = self.client_id + ':' + self.client_secret
        auth_bytes = auth_string.encode("utf-8")
        auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")

        return {
            "Authorization" : "Basic " + auth_base64,
            "Content-Type": "application/x-www-form-urlencoded"
        }

    # recommended by spotify documentation for security
    def generate_random_string(self):
        return ''.join(random.choices(self.characters, k=self.length))


    # requests user authorization and builds the url that the user would login to
    def build_user_login_url(self):
        state = self.generate_random_string()
        scope = 'user-read-private user-read-email user-read-playback-state user-modify-playback-state'

        query_params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'scope': scope,
            'redirect_uri': self.redirect_uri,
            'state': state,
            'show_dialog' : 'false'
        }

        return f"{self.auth_url}?{urllib.parse.urlencode(query_params)}"
    
    # added to assign user_id to account_id
    def get_user_profile(self):
        token = self.get_valid_access_token()

        headers = {
            "Authorization": f"Bearer {token}"
        }
        url = f"{self.base_url}me"

        response = requests.get(
            url,
            headers=headers
        )
        response.raise_for_status
        return response.json()

    def save_tokens(self, token_data):
        now = time.time()
        # update access token and expires_at to save the token used to call Spotify
        self.access_token = token_data.get("access_token")
        self.expires_at = now + token_data.get("expires_in", 3600) - 60

        # saves the refresh token if available
        if token_data.get("refresh_token"):
            self.refresh_token = token_data.get("refresh_token")
    
    def exchange_code_for_access_token(self, code):
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri
        }

        response = requests.post(
            self.token_url,
            headers=self.get_auth_header(),
            data=data,        
        )
        # call save_tokens to save needed token data
        response.raise_for_status()
        token_data = response.json()
        self.save_tokens(token_data)
        
        return token_data
    
    # obtain new access token when old access expires
    def refresh_access_token(self):
        if not self.refresh_token:
            raise RuntimeError("No refresh token. User must login again")

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }

        response = requests.post(
            self.token_url,
            headers=self.get_auth_header(),
            data=data
        )

        response_data = response.json()

        if not response.ok:
            if response_data.get("error") == "invalid_grant":
                self.access_token = None
                self.refresh_token = None
                self.expires_at = 0
                raise RuntimeError("Refresh token is invalid. User must log in again")

        if "refresh_token" not in response_data:
            response_data["refresh_token"] = self.refresh_token

        self.save_tokens(response_data)

        return response_data

    def get_valid_access_token(self):
        # if token is present and not expired
        if self.access_token and time.time() < self.expires_at:
            return self.access_token
        
        # if there is a refresh token we can obtain a new token
        if self.refresh_token:
            token_data = self.refresh_access_token()
            return token_data["access_token"]

        raise RuntimeError("There is no valid access token. User must log in.")

    # fetch track data and extract uris for web player
    def search_track(self, query):
        AUTH_URL = 'https://accounts.spotify.com/api/token'

        auth_response = requests.post(AUTH_URL, {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        })
        auth_response_data = auth_response.json()
        access_token = auth_response_data['access_token']
        headers = {'Authorization': 'Bearer {token}'.format(token=access_token)}

        # token = self.get_valid_access_token()
        # headers = {"Authorization": f"Bearer {token}"}
        # limit of 3 for dropdown implementation
        params = {"q": query, "type": "track", "limit": 5}

        response = requests.get(f"{self.base_url}search", headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            tracks = data.get("tracks", {}).get("items", [])
            results_list = []
            for track in tracks:
                album_images = track.get("album", {}).get("images", [])
                image_url = None
                # if album image exists assign image url to the first image
                if album_images:
                    image_url = album_images[0]["url"]

                results_list.append({
                    "name": track["name"],
                    "uri": track["uri"],
                    "artist": track["artists"][0]["name"],
                    "image": image_url
                })
            # returns a list containing up to 3 song objects
            return results_list
        return []
    
    # start playback of the user's chosen track on their specific Web Player SDK device ID
    def play_track(self, device_id, track_uri):
        token = self.get_valid_access_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        url = f"{self.base_url}me/player/play?device_id={device_id}"

        data = {
            "uris" : [track_uri]
        }

        response = requests.put(url, headers=headers, json=data)

        return response.status_code == 204





# testing
if __name__ == "__main__":
    spotify = SpotifyClient()

    query = input("search for song: ").strip()

    songs = spotify.search_track(query)

    print()

    for song in songs:
        print("name:", song["name"])
        print("artist:", song["artist"])
        print("uri:", song["uri"])
        print("image url:", song["image"])

