"""Function for recording audio from a microphone."""
import io
import typing
import time
import wave
from pathlib import Path

from __future__ import annotations

"""Utility for recording audio from a microphone until silence is detected."""

import io
import wave
import typing
import time
from pathlib import Path

from rhasspysilence import WebRtcVadRecorder
import pyaudio


def _buffer_to_wav(buffer: bytes, rate: int = 16000) -> bytes:
    """Wrap a raw PCM buffer in a WAV container.

    Args:
        buffer: raw audio bytes (16‑bit PCM, mono).
        rate: sampling rate.

    Returns:
        A bytes object containing a valid WAV file.
    """

    width = 2  # 16 bits
    channels = 1

    with io.BytesIO() as wav_buffer:
        wav_file: wave.Wave_write = wave.open(wav_buffer, mode="wb")
        with wav_file:
            wav_file.setframerate(rate)
            wav_file.setsampwidth(width)
            wav_file.setnchannels(channels)
            wav_file.writeframesraw(buffer)

        return wav_buffer.getvalue()


def speech_to_text(output_path: str | Path = "audio/recording.wav") -> Path:
    """Record from the default microphone until silence is detected.

    The recording is saved as a WAV file at ``output_path``. The directory is
    created if necessary.

    Returns:
        Path to the written WAV file.
    """

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    recorder = WebRtcVadRecorder(vad_mode=3, silence_seconds=4)
    recorder.start()

    pa = pyaudio.PyAudio()
    stream = pa.open(
        rate=16000,
        format=pyaudio.paInt16,
        channels=1,
        input=True,
        frames_per_buffer=960,
    )
    stream.start_stream()

    try:
        while True:
            chunk = stream.read(960, exception_on_overflow=False)
            voice_command = recorder.process_chunk(chunk)

            if voice_command:
                # we got a result (speech end or failure)
                audio_data = recorder.stop()
                wav_bytes = _buffer_to_wav(audio_data)
                output_path.write_bytes(wav_bytes)
                return output_path
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()


if __name__ == "__main__":
    print("Recording until silence, saving to audio/recording.wav")
    speech_to_text()
