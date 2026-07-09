# unit-testing for spotify_api.py file

import unittest
from unittest.mock import patch, Mock
from spotify_api import SpotifyClient

#def test_build_user_login_url()

def test_get_user_profile_returns_profile():
    spotify = SpotifyClient()
    spotify.access_token = "fake_access_token"
    spotify.expires_at = 9999999999

    fake_response = Mock()

    fake_response.status_code = 200

    fake_response.json.return_value = {
        #"id": 
    }