import os
from dotenv import load_dotenv
from google import genai

load_dotenv()


class Generator():
    # Sets up gemini client
    def __init__(self, model="gemini-3.1-flash-lite-preview"):
        api_key = os.getenv('GEMINI_API_KEY')
        genai.api_key = api_key
        self.client = genai.Client(api_key=api_key)
        self.model = model


class SongGenerator(Generator):
    # Calls to Gemini API to generate songs based off of saved data
    def get_songs(self, song, notes = None, location=None):

        note_data = {
        "song": song,
        "notes": notes,
        "location": location
        }

        interaction = self.client.interactions.create(
            model=self.model,
            input=(
                f"Give me 3 song recommendations based off of {note_data}. "
                "Respond with ONLY 3 lines, no numbering, no extra text, "
                "in this exact format:\n"
                "Song Name | Artist Name"
            ),
            system_instruction=(
                "You're the Spotify DJ"
            ),
        )

        # splits the output by title and artist and puts into a list
        songs = []
        for line in interaction.output_text.strip().split("\n"):
            line = line.strip()
            if "|" in line:
                name, artist = line.split("|", 1)
                songs.append({
                    "name":name.strip(),
                    "artist": artist.strip()
                })

        return songs 


# feature not being used currently
"""
class MoodInsightGenerator(Generator):
    # Gets data from entry data and returns a string 
    # that can be inputted into Gemini for context
    def format_data(month, day, year):
        entry = get_by_date(month, day, year)

        data = (
            f"Song: {entry.song_name}, "
            f"Song_link: {entry.spotify_link}, "
            f"Location: {entry.location_name}"
        )

        return data

    # Calls to Gemini API to give insight on mood based off entry info
    def get_mood_insights(self, song, notes = None, location=None):
        note_data = {
        "song": song,
        "notes": notes,
        "location": location
        }

        interaction = self.client.interactions.create(
            model=self.model,
            input=f"Tell me my mood and how I was feeling based off of {note_data} in two sentences",
            system_instruction=(
                "You are sympathetic and instrospective, taking your speech "
                "style from Spotify Wrapped"
            ),
        )

        return interaction.output_text
"""


# testing
if __name__ == "__main__":
    generator = MoodInsightGenerator()
    mood = generator.get_mood_insights("Bohemian Rapsody")
    print(mood)
