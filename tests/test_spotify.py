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
        self.assertIn("show_dialog=true", result_url)

    @patch("spotify_api.requests.get")
    @patch("spotify_api.SpotifyClient.get_valid_access_token")
    def test_get_user_profile_returns_profile(self, mock_get_token, mock_get_request):
        mock_get_token.return_value = "fake_access_token"
        spotify = SpotifyClient()
        spotify.base_url = "https://spotify.com"

        fake_profile_data = {
            "id": "spotify_user_100",
            "display_name": "Test User",
            "email":"test@example.com"
        }

        fake_response = Mock()
        fake_response.status_code = 200
        fake_response.json.return_value = fake_profile_data
        
        mock_get_request.return_value = fake_response

        profile = spotify.get_user_profile()

        self.assertEqual(profile["id"], "spotify_user_100")
        self.assertEqual(profile["display_name"], "Test User")

        expected_url = "https://spotify.comme"
        expected_headers = {"Authorization": "Bearer fake_access_token"}

        self.assertEqual(mock_get_request.call_args[0][0], expected_url)
        self.assertEqual(mock_get_request.call_args[1]['headers'], expected_headers)

        self.assertTrue(mock_get_request.called)
        self.assertTrue(fake_response.raise_for_status.called)

if __name__ == '__main__':
    unittest.main()