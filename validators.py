import os

def validate_image_path(image_file_path):
    if not os.path.exists(image_file_path):
        print(f"Error: Image file not found at '{image_file_path}'")
        print("Please update 'image_file_path' or ensure the image is in the same directory.")
        return False
    return True

def validate_api_key():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        print("Please obtain your Gemini API key from Google AI Studio (https://aistudio.google.com/app/apikey)")
        print("Example: export GEMINI_API_KEY='your_api_key_here'")
        return None
    return api_key
