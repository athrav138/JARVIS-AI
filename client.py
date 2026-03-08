"""Minimal example showing how to talk to the chat API.

This file isn't used by the main application; it's just here as a
reference when you're experimenting interactively.
"""

import os
import sys

try:
    import openai
except ImportError:  # pragma: no cover - simple example
    sys.exit("install openai (`pip install openai`)")

if __name__ == "__main__":
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        sys.exit("OPENAI_API_KEY environment variable not set")

    openai.api_key = api_key
    resp = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a virtual assistant named Jarvis."},
            {"role": "user", "content": "What is coding?"},
        ],
    )
    print(resp.choices[0].message["content"])
