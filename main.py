"""Main file for the Jarvis personal assistant project.

The application listens to the microphone, sends the audio to Deepgram for
transcription, asks OpenAI for a response, converts that response to speech
with ElevenLabs, and plays it back while logging the conversation and status.
"""

from __future__ import annotations

import os
import asyncio
import sys
from pathlib import Path
from time import perf_counter
from typing import Union

from dotenv import load_dotenv
import openai
from deepgram import Deepgram
import pygame
from pygame import mixer
import elevenlabs

from record import speech_to_text


# ---------------------------------------------------------------------------
# configuration / initialization
# ---------------------------------------------------------------------------

load_dotenv()  # read .env file if present

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

if not OPENAI_API_KEY or not DEEPGRAM_API_KEY or not ELEVENLABS_API_KEY:
    sys.exit("Missing one or more required API keys; check your .env file.")

openai.api_key = OPENAI_API_KEY
client = openai.ChatCompletion

deepgram = Deepgram(DEEPGRAM_API_KEY)

elevenlabs.set_api_key(ELEVENLABS_API_KEY)

# pygame mixer must be initialised before use
mixer.init()

# personality fingerprint passed to the model.  You can tweak it freely.
PROMPT_PREFIX = (
    "You are Jarvis, Alex's human assistant. You are witty and full of personality. "
    "Keep your answers short (one or two sentences)."
)

conversation_history: list[dict] = []

# the file where recorded audio is stored by ``record.speech_to_text``
RECORDING_PATH = Path("audio/recording.wav")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def log(msg: str) -> None:
    """Write status both to stdout and to ``status.txt`` so the display app
    can pick it up.
    """

    print(msg)
    with open("status.txt", "w", encoding="utf-8") as f:
        f.write(msg)


async def transcribe(file_path: Union[str, Path]) -> str:
    """Ask Deepgram to transcribe the given WAV file.

    The current code prefers the "transcript" field when available for
    convenience; the original version built a string from individual word
    dictionaries which is more verbose.
    """

    with open(file_path, "rb") as audio:
        source = {"buffer": audio, "mimetype": "audio/wav"}
        result = await deepgram.transcription.prerecorded(source)
        return result["results"]["channels"][0]["alternatives"][0].get(
            "transcript", ""
        )


def request_gpt(user_input: str) -> str:
    """Send the provided message (plus history) to the OpenAI chat API and
    return the assistant's reply.
    """

    messages = [
        {"role": "system", "content": PROMPT_PREFIX},
    ]
    messages += conversation_history
    messages.append({"role": "user", "content": user_input})

    resp = client.create(model="gpt-3.5-turbo", messages=messages)
    text = resp.choices[0].message["content"].strip()
    # update history so future calls see the conversation
    conversation_history.append({"role": "user", "content": user_input})
    conversation_history.append({"role": "assistant", "content": text})
    return text


def speak(text: str, voice: str = "Adam") -> Path:
    """Use ElevenLabs to generate and save audio for ``text``.

    Returns the path to the WAV file that was created.
    """

    audio = elevenlabs.generate(text=text, voice=voice, model="eleven_monolingual_v1")
    output = Path("audio/response.wav")
    output.parent.mkdir(exist_ok=True)
    elevenlabs.save(audio, str(output))
    return output


# ---------------------------------------------------------------------------
# main loop
# ---------------------------------------------------------------------------


def main() -> None:
    log("Starting Jarvis assistant")
    try:
        while True:
            log("Listening...")
            recorded = speech_to_text(RECORDING_PATH)
            log("Done listening")

            start = perf_counter()
            transcript = asyncio.run(transcribe(recorded))
            elapsed = perf_counter() - start
            log(f"Finished transcribing in {elapsed:.2f} seconds.")

            if not transcript:
                log("No speech detected, retrying...")
                continue

            with open("conv.txt", "a", encoding="utf-8") as f:
                f.write(transcript + "\n")

            start = perf_counter()
            response = request_gpt(transcript)
            elapsed = perf_counter() - start
            log(f"Finished generating response in {elapsed:.2f} seconds.")

            start = perf_counter()
            wav_path = speak(response)
            elapsed = perf_counter() - start
            log(f"Finished generating audio in {elapsed:.2f} seconds.")

            log("Speaking...")
            sound = mixer.Sound(str(wav_path))
            with open("conv.txt", "a", encoding="utf-8") as f:
                f.write(response + "\n")
            sound.play()
            pygame.time.wait(int(sound.get_length() * 1000))

            print(f"\n --- USER: {transcript}\n --- JARVIS: {response}\n")

    except KeyboardInterrupt:
        log("Shutting down")


if __name__ == "__main__":
    main()
