# Code-By-Voice

A Python program for voice-controlled typing using the Vosk speech recognition engine.

## Features

- Start dictation with the wake word: **Jarvis**
- End dictation with any of the following phrases:
  - Jarvis done
  - Jarvis send
  - Jarvis go
  - Jarvis enter
  - Jarvis finish
- Automatically types the transcribed text into the focused window
- Easy to use, works on Windows

## Requirements

- Python 3.7+
- [Vosk](https://alphacephei.com/vosk/) speech recognition library
- [sounddevice](https://python-sounddevice.readthedocs.io/)
- [pyautogui](https://pyautogui.readthedocs.io/)
- Vosk English model (see below)

## Installation

### Using Conda (Recommended)

1. **Create the environment:**
   ```sh
   conda env create -f environment.yml
   ```
2. **Activate the environment:**
   ```sh
   conda activate code-by-voice
   ```

### Using pip (Alternative)

1. **Install dependencies:**
   ```sh
   pip install vosk sounddevice pyautogui
   ```

## Download the Vosk Model

1. Go to [Vosk Models](https://alphacephei.com/vosk/models)
2. Download `vosk-model-small-en-us-0.15` (or a larger model for better accuracy)
3. Extract the model to the `models/` directory so the path is:
   ```
   models/vosk-model-small-en-us-0.15/
   ```

## Usage

1. **Focus the text box or window where you want the text to be typed.**
2. **Run the program:**
   ```sh
   python transcribe_vosk.py
   ```
3. **Follow the instructions in the terminal:**
   - Say **"Jarvis"** to start dictation.
   - Speak your message.
   - End with any of: **"Jarvis done"**, **"Jarvis send"**, **"Jarvis go"**, **"Jarvis enter"**, or **"Jarvis finish"**.
   - The program will type your message and press Enter.

## Example

Say:
```
Jarvis write hello world jarvis send
```
The program will type: `write hello world` and press Enter.

## Using with AI Agents and Copilots

This project is compatible with modern AI-powered coding environments such as **Cursor**, **GitHub Copilot**, and other AI copilots. You can use Code-By-Voice to:

- **Dictate code, commands, or documentation** directly into your editor using your voice.
- **Combine voice control with AI assistance** for a hands-free, productivity-boosting workflow.
- **Leverage Cursor's AI agent** or other copilots to generate, refactor, or explain code, while using your voice to trigger actions or input text.

### Example Workflow

1. **Start Code-By-Voice** and focus your Cursor editor or terminal.
2. **Say:**  
   Jarvis write a Python function that adds two numbers jarvis send
   The text will be typed into your editor.
3. **Let your AI copilot (e.g., Cursor AI, Copilot, ChatGPT) complete, refactor, or explain the code as needed.**
4. **Use your voice to continue coding, documenting, or running commands.**

### Benefits

- **Hands-free coding:** Great for accessibility, multitasking, or reducing repetitive strain.
- **Seamless integration:** Works with any editor or tool that accepts keyboard input.
- **AI + Voice:** Combine the power of AI code generation with natural language voice input.

## Notes

- Make sure your microphone is working and set as the default input device.
- The program will not work without the Vosk model in the correct directory.
- Large model files and temporary files should not be committed to the repository. See `.gitignore` for details.

## License

MIT (or your preferred license) 