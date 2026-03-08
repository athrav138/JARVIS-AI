import speech_recognition as sr
import webbrowser
import pyttsx3
import musicLibrary
import requests
from openai import OpenAI

# dotenv support (optional)
import os
from gtts import gTTS
import pygame
import os

# pip install pocketsphinx

recognizer = sr.Recognizer()
engine = pyttsx3.init() 
# load environment variables from .env if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# API key used by OpenAI. Prefer to set OPENAI_API_KEY in your environment
API_KEY = os.getenv("OPENAI_API_KEY") or ""

# News API key (can be same as above or different)
newsapi = os.getenv("NEWSAPI_KEY") or API_KEY

if not API_KEY:
    print("Warning: OPENAI_API_KEY is not set. AI features will fail.")


def speak_old(text):
    engine.say(text)
    engine.runAndWait()

def speak(text):
    tts = gTTS(text)
    tts.save('temp.mp3') 

    # Initialize Pygame mixer
    pygame.mixer.init()

    # Load the MP3 file
    pygame.mixer.music.load('temp.mp3')

    # Play the MP3 file
    pygame.mixer.music.play()

    # Keep the program running until the music stops playing
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    
    pygame.mixer.music.unload()
    os.remove("temp.mp3") 

def aiProcess(command):
    client = OpenAI(api_key=API_KEY)
    

    completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "You are a virtual assistant named jarvis skilled in general tasks like Alexa and Google Cloud. Give short responses please"},
        {"role": "user", "content": command}
    ]
    )

    return completion.choices[0].message.content

def processCommand(c: str):
    """Handle a single textual command from the user.

    Supported phrases:
      - "open google", "open facebook", "open youtube", "open linkedin"
      - "play <song>" : opens a YouTube link from musicLibrary.music
      - any string containing "news" : fetches headlines from NewsAPI
      - anything else is forwarded to OpenAI via :func:`aiProcess`
    """

    text = c.lower()

    if "open google" in text:
        webbrowser.open("https://google.com")

    elif "open facebook" in text:
        webbrowser.open("https://facebook.com")

    elif "open youtube" in text:
        webbrowser.open("https://youtube.com")

    elif "open linkedin" in text:
        webbrowser.open("https://linkedin.com")

    elif text.startswith("play"):
        parts = text.split()
        if len(parts) < 2:
            speak("Please tell me which song to play.")
            return
        song = parts[1]
        link = musicLibrary.music.get(song)
        if link:
            webbrowser.open(link)
        else:
            speak(f"I don't know the song {song}.")

    elif "news" in text:
        # use the shared API_KEY for the News API as well
        try:
            r = requests.get(
                f"https://newsapi.org/v2/top-headlines?country=in&apiKey={newsapi}"
            )
            r.raise_for_status()
        except Exception as exc:
            speak("Sorry, I couldn't fetch the news right now.")
            print("News API error", exc)
            return

        data = r.json()
        articles = data.get('articles', [])
        for article in articles:
            speak(article.get('title', ''))

    else:
        # Let OpenAI handle the request
        output = aiProcess(c)
        speak(output)





def run():
    """Start the voice loop; this is the entry point when executed as a script."""
    speak("Initializing Jarvis....")
    while True:
        # Listen for the wake word "Jarvis"
        # obtain audio from the microphone
        r = sr.Recognizer()

        print("recognizing...")
        try:
            with sr.Microphone() as source:
                print("Listening...")
                audio = r.listen(source, timeout=2, phrase_time_limit=1)
            word = r.recognize_google(audio)
            if word.lower() == "jarvis":
                speak("Ya")
                # Listen for command
                with sr.Microphone() as source:
                    print("Jarvis Active...")
                    audio = r.listen(source)
                    command = r.recognize_google(audio)

                    processCommand(command)

        except Exception as e:
            print("Error; {0}".format(e))


if __name__ == "__main__":
    run()


