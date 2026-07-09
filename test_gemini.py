# Unit tests for SongGenerator


import unittest
from unittest.mock import patch, MagicMock
from gemini import SongGenerator

class TestSongGenerator(unittest.TestCase):

    @patch('gemini.genai.Client')
    def test_valid_get_songs(self, mock_gemini_client):
        # fake the Gemini client so no real API call happens
        mock_instance = MagicMock()
        mock_gemini_client.return_value = mock_instance

        # Fake output for what self.client.interactions.create(...) returns
        f_response = MagicMock()
        f_response.output_text = (
            "Bohemian Rhapsody | Queen\n"
            "Africa | Toto\n"
            "Landslide | Fleetwood Mac"
        )

        # Makes sure to not run gemini interactions API and just get f_response
        mock_instance.interactions.create.return_value = f_response

        generator = SongGenerator()
        songs = generator.get_songs("Test Song", notes="Feeling nostalgic", location="Seattle")

        self.assertEqual(len(songs), 3)
        self.assertEqual(songs[0], {"name": "Bohemian Rhapsody", "artist": "Queen"})
        self.assertEqual(songs[1], {"name": "Africa", "artist": "Toto"})
        self.assertEqual(songs[2], {"name": "Landslide", "artist": "Fleetwood Mac"})


    @patch('gemini.genai.Client')
    def test_invalid_get_songs(self, mock_gemini_client):
        # fake the Gemini client so no real API call happens
        mock_instance = MagicMock()
        mock_gemini_client.return_value = mock_instance

        # Fake output for what self.client.interactions.create(...) returns
        f_response = MagicMock()
        f_response.output_text = (
            "Here are your recommendations:\n"
            "\n"
            "Bohemian Rhapsody | Queen\n"
            "Africa Toto\n"
            "Landslide | Fleetwood Mac"
        )

        # Makes sure to not run gemini interactions API and just get f_response
        mock_instance.interactions.create.return_value = f_response

        generator = SongGenerator()
        songs = generator.get_songs("Test Song", notes="Feeling nostalgic", location="Seattle")

        self.assertEqual(len(songs), 2)
        self.assertEqual(songs[0], {"name": "Bohemian Rhapsody", "artist": "Queen"})
        self.assertEqual(songs[1], {"name": "Landslide", "artist": "Fleetwood Mac"})

if __name__ == "__main__":
    unittest.main()