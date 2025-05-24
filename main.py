import os
import time
import tempfile
import pyautogui
import sounddevice as sd
import wave
import openai
from dotenv import load_dotenv

# Record audio from the microphone and save as WAV
def record_audio(filename, duration=10, fs=44100):
    print(f"Recording for {duration} seconds...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16 bits = 2 bytes
        wf.setframerate(fs)
        wf.writeframes(audio.tobytes())
    print(f"Audio saved to {filename}")

# Transcribe audio using OpenAI Whisper API via openai client
def transcribe_audio(filename, api_key):
    openai.api_key = api_key
    print("Transcribing audio...")
    with open(filename, "rb") as audio_file:
        transcript = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    return transcript.text

if __name__ == "__main__":
    # Load environment variables from .env
    load_dotenv()
    # Get OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set in the environment variables env.yml")

    print("You have 5 seconds to focus the target textbox...")
    time.sleep(5)
    # Type the text if transcription succeeded
    while True:
        # Record audio
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            audio_path = tmp.name
        record_audio(audio_path)
        text = transcribe_audio(audio_path, api_key)
        print(f"Transcribed text: {text}")
        pyautogui.write(text)
        pyautogui.press('enter')
        time.sleep(20)

    # Clean up
    os.remove(audio_path) 