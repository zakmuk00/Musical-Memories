from dotenv import load_dotenv
from google import genai
import os

load_dotenv()

# Sets up gemini client
my_api_key = os.getenv('GENAI_KEY')
genai.api_key = my_api_key
client = genai.Client()

stream = client.interactions.create(
    model="gemini-3.5-flash",
    input="Explain how AI works",
    stream=True
)
for event in stream:
    if event.event_type == "step.delta":
        if event.delta.type == "text":
            print(event.delta.text, end="")
