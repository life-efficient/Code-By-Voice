import sounddevice as sd
import tempfile
import wave
from playsound import playsound
import os
import openai

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

def callback(indata, frames, time, status, q):
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

def play_sound(sound_path):
    try:
        playsound(sound_path)
    except Exception as e:
        print(f"Could not play sound: {e}")

def speak_with_openai_tts(text, voice="alloy"):
    response = openai.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text
    )
    # Save the audio to a temp file and play it
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmpfile:
        tmpfile.write(response.content)
        tmpfile.flush()
        os.system(f"afplay '{tmpfile.name}'")  # macOS; use another player for other OSes
    os.remove(tmpfile.name) 