import os
from dotenv import load_dotenv
from google import genai
# from entry import get_by_date, get_by_id

load_dotenv()


class MoodInsightGenerator():

    # Sets up gemini client
    def __init__(self, model="gemini-3.5-flash"):
        api_key = os.getenv('GENAI_KEY')
        genai.api_key = api_key
        self.client = genai.Client()
        self.model = model

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
    def get_mood_insights(self):
        data = "Song: Karma Police, Song_link: https://open.spotify.com/track/63OQupATfueTdZMWTxW03A?si=3874c5edd575475d, Location: Yosemite"
        #data = format_data(7, 10, 2026)
        # f data is None:
            # print("Error no data")

        stream = self.client.interactions.create(
            model=self.model,
            input=f"In three sentences tell me how I was feeling based off of {data}",
            system_instruction=(
                "You are sympathetic and instrospective, taking your speech "
                "style from Spotify Wrapped"
            ),
            stream=True
        )

        for event in stream:
            if event.event_type == "step.delta":
                if event.delta.type == "text":
                    print(event.delta.text, end="")

if __name__ == "__main__":
    generator = MoodInsightGenerator()
    generator.get_mood_insights()
