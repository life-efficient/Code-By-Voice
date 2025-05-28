import os
import time
import pyautogui


def focus_and_click_app(app_name: str, field_image_path: str, confidence: float = 0.8, wait_time: float = 1.0):
    """
    Brings the specified app to the foreground (or opens it if not running),
    then locates and clicks the input field specified by an image.
    """
    time.sleep(3)
    # macOS: use 'open -a' to bring app to front or open it
    os.system(f"open -a '{app_name}'")
    time.sleep(wait_time)  # Wait for app to come to front

    # Locate the input field on the screen
    location = pyautogui.locateCenterOnScreen(field_image_path, confidence=confidence)
    if location:
        print("location", location)
        pyautogui.click(1200, 830)
        print(f"Clicked input field in {app_name}!")
        return True
    else:
        print(f"Could not find the input field on the screen for {app_name}.")
        return False


def focus_cursor_and_click_prompt_box():
    """
    Focuses the Cursor app and clicks at the hardcoded coordinates of the prompt box.
    Update the coordinates as needed for your setup.
    """
    app_name = "Cursor"
    prompt_box_coords = (1200, 830)  # Update these coordinates as needed
    os.system(f"open -a '{app_name}'")
    time.sleep(1.5)  # Wait for app to come to front
    pyautogui.click(*prompt_box_coords)
    print(f"Clicked prompt box in {app_name} at {prompt_box_coords}!")
    return True


if __name__ == "__main__":
    # Place your screenshots for automation in the 'automation_target_images' folder.
    # Example: automation_target_images/input_field.png
    # image_path = os.path.join("automation_target_images", "input.png")
    # focus_and_click_app("Cursor", image_path)
    focus_cursor_and_click_prompt_box() 