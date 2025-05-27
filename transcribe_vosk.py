import os
import time
import json
import queue
import vosk
import sounddevice as sd
import pyautogui
import re

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

def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status)
    q.put(bytes(indata))

def transcribe_microphone():
        rec = vosk.KaldiRecognizer(model, samplerate)
        accumulated_text = []
        listening = False
        partial_accum = []
        WAKE_WORD = "jarvis"
        END_PHRASES = [
            "jarvis done",
            "jarvis send",
            "jarvis go",
            "jarvis enter",
            "jarvis finish"
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
            while True:
                data = q.get()
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    if listening and result["text"]:
                        accumulated_text.append(result["text"])
                else:
                    partial = json.loads(rec.PartialResult())
                    partial_text = partial.get("partial", "").lower()
                    if not listening:
                        # Wait for wake word
                        if WAKE_WORD in partial_text:
                            listening = True
                            partial_accum = []
                            accumulated_text = []
                            print("[Jarvis activated] Start speaking...")
                    else:
                        # Accumulate partials for end phrase detection
                        if partial_text:
                            partial_accum.append(partial_text)
                            # Keep only last 10 partials to avoid memory bloat
                            if len(partial_accum) > 10:
                                partial_accum.pop(0)
                            # Check for any end phrase in the last few partials
                            joined = " ".join(partial_accum).lower()
                            for end_phrase in END_PHRASES:
                                if end_phrase in joined:
                                    # Remove the end phrase from the output
                                    full_text = " ".join(accumulated_text)
                                    # Remove everything after the end phrase
                                    pattern = re.compile(rf"(.*?)\b{re.escape(end_phrase)}\b", re.IGNORECASE)
                                    match = pattern.search(full_text)
                                    if match:
                                        final_text = match.group(1).strip()
                                    else:
                                        final_text = full_text.strip()
                                    return final_text
  
   

def main():
    print("You have 5 seconds to focus the target textbox...")
    time.sleep(5)
    try:
        while True:
            text = transcribe_microphone()
            if text:
                print(f"Transcribed text: {text}")
                pyautogui.write(text)
                pyautogui.press('enter')
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nExiting program. Goodbye!") 
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

if __name__ == "__main__":
    main()