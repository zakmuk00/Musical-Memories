# unit-testing for spotify_api.py file

import unittest
from unittest.mock import patch, Mock
from spotify_api import SpotifyClient
import urllib.parse

class TestSpotifyClient(unittest.TestCase):

    # by pass generate string function
    @patch('spotify_api.SpotifyClient.generate_random_string')
    def test_build_user_login_url(self, mock_generate_string):
        # mock return value for random state string
        mock_generate_string.return_value = "fixed_mock_state_123"

        spotify = SpotifyClient()
        spotify.client_id = "test_client_id"
        spotify.redirect_uri = "http://localhost:5000/callback"
        spotify.auth_url = "https://spotify.com"

        result_url = spotify.build_user_login_url()

        self.assertTrue(result_url.startswith("https://spotify.com"))
        self.assertIn("response_type=code", result_url)
        self.assertIn("client_id=test_client_id", result_url)
        self.assertIn("state=fixed_mock_state_123", result_url)
        self.assertIn("show_dialog=false", result_url)

"""
    @patch
    def test_get_user_profile_returns_profile():

        spotify = SpotifyClient()
        spotify.access_token = "fake_access_token"
        spotify.expires_at = 9999999999

        fake_response = Mock()

        fake_response.status_code = 200

        fake_response.json.return_value = {
            #"id":
        }
"""
if __name__ == '__main__':
    unittest.main()