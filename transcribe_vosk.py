import os
import time
import json
import queue
import vosk
import sounddevice as sd
import pyautogui
import re
import tempfile
import wave
import openai
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Initialize Vosk model
model_path = "models/vosk-model-small-en-us-0.15"  # Path to the extracted model folder
if not os.path.exists(model_path):
    print(f"Please download the model and extract it to: {model_path}")
    print("Download from: https://alphacephei.com/vosk/models")
    exit(1)

model = vosk.Model(model_path)
device_info = sd.query_devices(None, 'input')
samplerate = int(device_info['default_samplerate'])

# Create a queue to store audio data
q = queue.Queue()

openai.api_key = os.getenv("OPENAI_API_KEY")

# Helper to record audio to a WAV file
class AudioRecorder:
    def __init__(self, samplerate, channels=1):
        self.samplerate = samplerate
        self.channels = channels
        self.frames = []
        self.recording = False

    def start(self):
        self.frames = []
        self.recording = True

    def stop(self):
        self.recording = False

    def add(self, data):
        if self.recording:
            self.frames.append(data)

    def save(self, filename):
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit audio
            wf.setframerate(self.samplerate)
            wf.writeframes(b''.join(self.frames))


def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status)
    q.put(bytes(indata))

def transcribe_with_openai(audio_path):
    with open(audio_path, "rb") as audio_file:
        transcript = openai.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=audio_file
        )
    return transcript.text if hasattr(transcript, 'text') else transcript

def transcribe_microphone():
    rec = vosk.KaldiRecognizer(model, samplerate)
    WAKE_WORD = "jarvis"
    END_PHRASES = [
        "jarvis done",
        "jarvis send",
        "jarvis go",
        "jarvis enter",
        "jarvis finish",
        "over"
    ]
    print(
        "Say 'Jarvis' to start dictation.\n"
        "End with :'\n" 
        "Jarvis done'\n"
        "Jarvis send'\n"
        "Jarvis go'\n"
        "Jarvis enter'\n"
        "Jarvis finish'\n"
        "Press Ctrl+C to stop."
    )
    with sd.RawInputStream(samplerate=samplerate, blocksize=8000, device=None,
                         dtype='int16', channels=1, callback=callback):
        listening = False
        partial_accum = []
        recorder = AudioRecorder(samplerate)
        while True:
            data = q.get()
            if listening:
                recorder.add(data)
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                if not listening:
                    # Wait for wake word
                    if WAKE_WORD in result["text"].lower():
                        listening = True
                        partial_accum = []
                        recorder.start()
                        print("[Jarvis activated] Start speaking...")
                else:
                    # Check for end phrase
                    full_text = result["text"].lower()
                    for end_phrase in END_PHRASES:
                        if end_phrase in full_text:
                            listening = False
                            recorder.stop()
                            print("[Jarvis deactivated] Processing...")
                            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
                                recorder.save(tmpfile.name)
                                print(f"Saved audio to {tmpfile.name}")
                                transcript = transcribe_with_openai(tmpfile.name)
                                print(f"OpenAI Transcript: {transcript}")
                                pyautogui.write(transcript)
                                # pyautogui.press('enter')  # Uncomment to press enter after typing
                            break
            else:
                partial = json.loads(rec.PartialResult())
                partial_text = partial.get("partial", "").lower()
                if not listening:
                    if WAKE_WORD in partial_text:
                        listening = True
                        partial_accum = []
                        recorder.start()
                        print("[Jarvis activated] Start speaking...")
                else:
                    if partial_text:
                        partial_accum.append(partial_text)
                        if len(partial_accum) > 10:
                            partial_accum.pop(0)
                        joined = " ".join(partial_accum).lower()
                        for end_phrase in END_PHRASES:
                            if end_phrase in joined:
                                listening = False
                                recorder.stop()
                                print("[Jarvis deactivated] Processing...")
                                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
                                    recorder.save(tmpfile.name)
                                    print(f"Saved audio to {tmpfile.name}")
                                    transcript = transcribe_with_openai(tmpfile.name)
                                    print(f"OpenAI Transcript: {transcript}")
                                    pyautogui.write(transcript)
                                    # pyautogui.press('enter')  # Uncomment to press enter after typing
                                break

def main():
    print("You have 5 seconds to focus the target textbox...")
    time.sleep(5)
    try:
        while True:
            transcribe_microphone()
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nExiting program. Goodbye!") 
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

if __name__ == "__main__":
    main()