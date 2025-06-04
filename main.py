import os
import google.generativeai as genai
from google.generativeai import types
from PIL import Image # Pillow library for image processing

def generate_with_image_input():
    # --- Configuration ---
    # Replace with the actual path to your image file
    image_file_path = '67.jpg' # Ensure this file exists in the same directory as your script

    # --- Validate Image Path ---
    if not os.path.exists(image_file_path):
        print(f"Error: Image file not found at '{image_file_path}'")
        print("Please update 'image_file_path' to the correct location or ensure the image is in the same directory.")
        return # Use return instead of exit() for cleaner function termination

    # --- Validate API Key ---
    # It's highly recommended to load your API key from environment variables for security.
    # Set it like: export GEMINI_API_KEY="YOUR_API_KEY_HERE" in your terminal
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        print("Please obtain your Gemini API key from Google AI Studio (https://aistudio.google.com/app/apikey) and set it.")
        print("Example: export GEMINI_API_KEY='your_api_key_here'")
        return

    # Configure the Google Generative AI client with your API key
    genai.configure(api_key=api_key)

    # --- Choose the Model ---
    model_name = "gemini-2.5-flash-preview-05-20" # Or "gemini-pro-vision"
    try:
        model = genai.GenerativeModel(model_name)
    except Exception as e:
        print(f"Error: Could not load model '{model_name}'. Please check the model name and your API key.")
        print(f"Details: {e}")
        return

    # --- Prepare the image for Gemini ---
    image_part = None # Initialize to None

    try:
        print(f"\nAttempting to prepare image: '{image_file_path}'")
        # The recommended way to handle image uploads for the Gemini API
        # This handles reading bytes, determining MIME type, and preparing the file.
        image_part = genai.upload_file(path=image_file_path)
        print("Successfully prepared image using genai.upload_file.")

    except Exception as e:
        print(f"An error occurred while preparing the image for Gemini: {e}")
        print("Please ensure 'google-generativeai' is installed and up-to-date (pip install --upgrade google-generativeai).")
        print("Also, confirm the image file is valid and readable.")
        return

    # If image_part is None, it means an error occurred during preparation
    if image_part is None:
        print("Failed to prepare image for Gemini. Exiting.")
        return

    # --- Construct the prompt for Gemini ---
    prompt_text = "Extract the Malayalam text from this image and translate it into English. If the text is not Malayalam, or if it's unreadable, please state that."

    prompt_text = "Describe the image in detail, focusing on the Malayalam text present. If the text is not Malayalam or is unreadable, please state that clearly."

    # Pass the text prompt and the image part directly as elements in a list.
    contents = [
        prompt_text,
        image_part
    ]

    # --- Configure generation settings (optional but good practice) ---
    # Use types.GenerationConfig for generation parameters (like temperature, max_output_tokens).
    generation_config = types.GenerationConfig(
        response_mime_type="text/plain",
        # You can add parameters like:
        # temperature=0.7,  # Controls randomness. Lower for more deterministic, higher for more creative.
        # max_output_tokens=2048, # Max tokens in the response.
        # top_p=0.95,       # Nucleus sampling.
        # top_k=40,         # Top-k sampling.
    )

    print("\n--- Sending request to Gemini... ---")
    print("--- Gemini's Response ---")
    try:
        # Stream the response for better user experience with potentially long outputs
        for chunk in model.generate_content(
            contents=contents,
            generation_config=generation_config, # Pass the generation_config object here
            stream=True # Enable streaming
        ):
            # Print each chunk of text as it arrives
            print(chunk.text, end="")
        print() # Add a newline at the end for clean output
    except Exception as e:
        print(f"\nError during Gemini API call: {e}")
        print("Possible issues: Incorrect API key, model not found, rate limits, or network problems.")
        print("Consider checking Google AI Studio's dashboard for API key status and usage.")


if __name__ == "__main__":
    generate_with_image_input()