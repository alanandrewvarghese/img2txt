import os
from validators import validate_image_path, validate_api_key
from image_loader import load_image
from gemini import configure_genai, get_gemini_model, generate_gemini_content
from formatter import parse_and_format_gemini_output

def generate_with_image_input():
    # --- Configuration ---
    image_file_path = '67.jpg'  # Ensure this file exists
    
    # --- Validate Image Path ---
    if not validate_image_path(image_file_path):
        return

    # --- Validate API Key ---
    api_key = validate_api_key()
    if not api_key:
        return

    # Configure the API
    configure_genai(api_key)

    # --- Choose the Model ---
    model_name = "gemini-2.5-flash-preview-05-20"  
    model = get_gemini_model(model_name)
    if not model:
        return

    # --- Prepare the image ---
    img = load_image(image_file_path)
    if not img:
        return

    # --- Construct the prompt ---
    prompt = """
    Analyze this image and:
    1. Identify if it contains Malayalam text (bible verse)
    2. If Malayalam text is present, extract it and provide English translation
    3. If no Malayalam text or unreadable, state that clearly
    4. Title should be the bible verse reference
    5. Provide alternative text for the main content (strictly exclude logo details) if applicable

    
    Respond in this JSON format:
    {
        "contains_malayalam": boolean,
        "title": "string or null",
        "extracted_bible_verse_malayalam": "string or null",
        "bible_verse_english_translation": "string or null",
        "alternative_text_for_main_content": "string or null",
        "confidence_level": "low/medium/high",
        "notes": "any additional observations"
    }
    """

    # --- Generate content ---
    gemini_response = generate_gemini_content(model, prompt, img)
    
    # --- Format and print the response ---
    if gemini_response:
        formatted_data = parse_and_format_gemini_output(gemini_response)
        if formatted_data:
            print("\n--- Formatted Response ---")
            print(formatted_data)
        else:
            print("Error: Could not format Gemini response.")

if __name__ == "__main__":
    generate_with_image_input()