import numpy as np
import sounddevice as sd
from agents.voice import AudioInput, SingleAgentVoiceWorkflow, VoicePipeline
from agent import jarvis
from agents import trace
import asyncio
import vosk
import queue
import os
from scipy.io import wavfile



# Function to play sound files (WAV only, using sounddevice and scipy.io.wavfile)
def play_sound(filename):
    base, ext = os.path.splitext(filename)
    wav_path = os.path.join('sounds', base + '.wav')
    if not os.path.exists(wav_path):
        print(f"Sound file not found: {wav_path}")
        return
    try:
        samplerate, data = wavfile.read(wav_path)
        sd.play(data, samplerate=samplerate)
        sd.wait()
    except Exception as e:
        print(f"Could not play sound {wav_path}: {e}")

async def voice_assistant():
    samplerate = int(sd.query_devices(kind='input')['default_samplerate'])
    model_path = "models/vosk-model-small-en-us-0.15"  # Updated to use the larger Vosk model
    model = vosk.Model(model_path)
    q = queue.Queue()

    def callback(indata, frames, time, status):
        q.put(bytes(indata))

    print("Say 'Jarvis' to start speaking, and say one of: 'Jarvis go', 'Jarvis end', 'Jarvis send', 'Jarvis over', or 'Jarvis finish' to finish and send your command.")

    while True:
        pipeline = VoicePipeline(workflow=SingleAgentVoiceWorkflow(jarvis))
        rec = vosk.KaldiRecognizer(model, samplerate)
        print("Waiting for wake word 'Jarvis'...")
        with sd.RawInputStream(samplerate=samplerate, blocksize = 8000, dtype='int16', channels=1, callback=callback):
            recording = []
            triggered = False
            while True:
                data = q.get()
                if rec.AcceptWaveform(data):
                    result = rec.Result()
                    if not triggered and 'jarvis' in result.lower():
                        print("Wake word detected. Start speaking...")
                        play_sound('positive')  # Play start listening sound (WAV only)
                        triggered = True
                        recording = []
                        continue
                    if triggered and any(x in result.lower() for x in ['jarvis go', 'jarvis end', 'jarvis send', 'jarvis over', 'jarvis finish']):
                        print("End word detected. Processing...")
                        play_sound('loading')  # Play start processing sound (WAV only)
                        break
                if triggered:
                    recording.append(np.frombuffer(data, dtype=np.int16))
        if not triggered:
            continue
        if len(recording) == 0:
            print("No speech detected.")
            play_sound('error')  # Play error sound (WAV only)
            continue
        recording = np.concatenate(recording, axis=0)
        audio_input = AudioInput(buffer=recording)
        with trace("ACME App Voice Assistant"):
            result = await pipeline.run(audio_input)
        response_chunks = []
        async for event in result.stream():
            if event.type == "voice_stream_event_audio":
                response_chunks.append(event.data)
        response_audio = np.concatenate(response_chunks, axis=0)
        print("Assistant is responding...")
        play_sound('whip')  # Play end/response sound (WAV only)
        sd.play(response_audio, samplerate=samplerate/2)
        sd.wait()
        print("---")

# Run the voice assistant
if __name__ == "__main__":
    asyncio.run(voice_assistant())