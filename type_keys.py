import pyautogui
import time

# Wait a few seconds to give the user time to focus the target window
print("You have 5 seconds to focus the target window...")
time.sleep(5)

# The text you want to type
type_text = "Hello, this is automated typing!"

# Type the text
pyautogui.write(type_text, interval=0.1)  # interval adds a small delay between key presses

# Optionally, press Enter at the end
pyautogui.press('enter') 