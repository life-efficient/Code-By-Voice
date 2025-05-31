import os
import time
import json
import queue
import vosk
import sounddevice as sd
import re
import tempfile
import wave
import openai
from dotenv import load_dotenv
from playsound import playsound
import requests
import get_tools as get_tools  # Import the get_tools module
import pprint
from supabase_auth import get_supabase_access_token
from audio_utils import AudioRecorder, callback, transcribe_with_openai, play_sound, speak_with_openai_tts

# Load environment variables from .env
load_dotenv()

token = get_supabase_access_token()
print(token)

client = openai.OpenAI()

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

# Use get_tools to load tool definitions
schema, schema_url = get_tools.fetch_openapi_schema()
TOOLS = get_tools.extract_tool_definitions(schema, schema_url)
OPENAI_TOOLS = get_tools.extract_openai_tools(TOOLS)

def run_tool_call(tool_call):
    """Executes a tool call (currently only HTTP tools)."""
    call = tool_call['call']
    if call['type'] == 'http':
        url = call['host'] + call['path']
        method = call['method'].upper()
        params = tool_call.get('parameters', {})
        headers = {"Authorization": f"Bearer {token}"}  # Add Bearer token to all requests
        # Remove parameters that are part of the path
        path_params = {}
        for key in list(params.keys()):
            if '{' + key + '}' in call['path']:
                url = url.replace('{' + key + '}', str(params[key]))
                path_params[key] = params.pop(key)
        try:
            if method == 'GET':
                resp = requests.get(url, params=params, headers=headers)
            elif method == 'POST':
                resp = requests.post(url, json=params, headers=headers)
            elif method == 'PATCH':
                resp = requests.patch(url, json=params, headers=headers)
            elif method == 'DELETE':
                resp = requests.delete(url, params=params, headers=headers)
            else:
                return f"Unsupported HTTP method: {method}"
            try:
                return resp.json()
            except Exception:
                return resp.text
        except Exception as e:
            return f"HTTP request failed: {e}"
    else:
        return f"Unsupported tool type: {call['type']}"

def process_transcript_and_respond(transcript):
    print(f"User said: {transcript}")
    response = client.responses.create(
        model="gpt-4.1-nano",
        input=[{"role": "user", "content": transcript}],
        tools=OPENAI_TOOLS,
        tool_choice="auto"
    )
    msg = response.output[0]
    if len(response.output) > 1:
        print('More response outputs than handled - look into this. len(response.output)', len(response.output))
        pprint.pprint(response.output)
        # raise NotImplementedError("Multiple messages in response - not yet handled")
    if msg.type == "function_call":
        tool_name = msg.name
        arguments = json.loads(msg.arguments)
        # Find the tool definition to get the call metadata
        tool_def = next((t for t in TOOLS if t['name'] == tool_name), None)
        if tool_def:
            tool_call = {"call": tool_def["call"], "parameters": arguments}
            tool_result = run_tool_call(tool_call)
            print('tool_result', tool_result)
            # Send tool result back to the model for a follow-up response
            tool_result_input = {
                "call_id": msg.call_id,
                "output": json.dumps(tool_result),
                "type": "function_call_output"
            }
            # Convert msg to dict for API input (use model_dump if available, else __dict__)
            try:
                function_call_suggestion = msg.model_dump()
            except AttributeError:
                function_call_suggestion = msg.__dict__
            followup = client.responses.create(
                model="gpt-4.1-nano",
                input=[
                    {"role": "user", "content": transcript},
                    function_call_suggestion,
                    tool_result_input
                ],
                tools=OPENAI_TOOLS,
                tool_choice="auto"
            )
            followup_msg = followup.output[0]
            if followup_msg.type == "message":
                for part in followup_msg.content:
                    if part.type == "output_text":
                        print(f"AI: {part.text}")
                        speak_with_openai_tts(part.text)
            else:
                print(f"Tool definition for {tool_name} not found.")
    elif msg.type == "message":
        print(f"AI: {msg.content[0].text}")
        speak_with_openai_tts(msg.content[0].text)

WAKE_WORD = "jarvis"

END_PHRASES = [
    "send it",
    "let's do it",
    "let's get it",
    "make it happen",
    "let's go",
    "over"
]

def handle_wake_word(text, listening, recorder, partial_accum):
    if WAKE_WORD in text:
        listening = True
        partial_accum.clear()
        recorder.start()
        play_sound('sounds/positive.m4a')
        print("[Jarvis activated] Start speaking...")
    return listening

def handle_end_phrase(text, listening, recorder):
    for end_phrase in END_PHRASES:
        if end_phrase in text:
            listening = False
            recorder.stop()
            play_sound('sounds/loading.m4a')
            print("[Jarvis deactivated] Processing...")
            return True, listening
    return False, listening

def handle_end_of_utterance(recorder):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
        recorder.save(tmpfile.name)
        print(f"Saved audio to {tmpfile.name}")
        transcript = transcribe_with_openai(tmpfile.name)
        play_sound('sounds/whip.m4a')
        process_transcript_and_respond(transcript)

def voice_loop():
    rec = vosk.KaldiRecognizer(model, samplerate)
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
                         dtype='int16', channels=1, callback=lambda indata, frames, time, status: callback(indata, frames, time, status, q)):
        listening = False
        partial_accum = []
        recorder = AudioRecorder(samplerate)
        while True:
            data = q.get()
            if listening:
                recorder.add(data)
            # Check if the recognizer has detected a final utterance (complete phrase)
            is_final_utterance = rec.AcceptWaveform(data)  # True if a complete phrase/utterance is ready, False if only a partial result
            if is_final_utterance:
                result = json.loads(rec.Result())
                text = result["text"].lower()
                if not listening:
                    listening = handle_wake_word(text, listening, recorder, partial_accum)
                else:
                    end_phrase_found, listening = handle_end_phrase(text, listening, recorder)
                    if end_phrase_found:
                        handle_end_of_utterance(recorder)
                        break
            else:
                partial = json.loads(rec.PartialResult())
                partial_text = partial.get("partial", "").lower()
                if not listening:
                    listening = handle_wake_word(partial_text, listening, recorder, partial_accum)
                else:
                    if partial_text:
                        partial_accum.append(partial_text)
                        if len(partial_accum) > 10:
                            partial_accum.pop(0)
                        joined = " ".join(partial_accum).lower()
                        end_phrase_found, listening = handle_end_phrase(joined, listening, recorder)
                        if end_phrase_found:
                            handle_end_of_utterance(recorder)
                            break

def main():
    # print("You have 5 seconds to focus the target textbox...")
    # time.sleep(5)
    try:
        while True:
            voice_loop()
            time.sleep(0.1)
    except KeyboardInterrupt:
        play_sound('sounds/disconnect.m4a')
        print("\nExiting program. Goodbye!")
    # except Exception as e:
    #     print(f"Error: {str(e)}")
    #     play_sound('sounds/disconnect.m4a')
    #     return None

if __name__ == "__main__":
    main()