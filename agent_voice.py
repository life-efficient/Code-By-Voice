import numpy as np
import sounddevice as sd
from agents.voice import AudioInput, SingleAgentVoiceWorkflow, VoicePipeline
from agent import jarvis
from agents import trace
import asyncio
from openai import OpenAI

async def voice_assistant():
    samplerate = sd.query_devices(kind='input')['default_samplerate']
    samplerate /= 2 # for some reason needed to prevent the agent hearing another language

    pipeline = VoicePipeline(
        workflow=SingleAgentVoiceWorkflow(jarvis),
    )

    while True:

        # Check for input to either provide voice or exit
        cmd = input("Press Enter to speak your query (or type 'esc' to exit): ")
        if cmd.lower() == "esc":
            print("Exiting...")
            break      
        print("Listening...")
        recorded_chunks = []

         # Start streaming from microphone until Enter is pressed
        with sd.InputStream(samplerate=samplerate, channels=1, dtype='int16', callback=lambda indata, frames, time, status: recorded_chunks.append(indata.copy())):
            input()
        print('recording done')

        # Concatenate chunks into single buffer
        recording = np.concatenate(recorded_chunks, axis=0)

        # Input the buffer and await the result
        audio_input = AudioInput(buffer=recording)
        with trace("ACME App Voice Assistant"):
            result = await pipeline.run(audio_input)
        response_chunks = []
        async for event in result.stream():
            if event.type == "voice_stream_event_audio":
                response_chunks.append(event.data)
        response_audio = np.concatenate(response_chunks, axis=0)
        print("Assistant is responding...")
        sd.play(response_audio, samplerate=samplerate)
        sd.wait()
        print("---")

# Run the voice assistant
if __name__ == "__main__":
    asyncio.run(voice_assistant())