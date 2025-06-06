import os
from typing import Optional, Dict
from pathlib import Path
from dotenv import load_dotenv

# Import your custom modules
from validators import validate_image_path, validate_api_key
from image_loader import load_image
from gemini import configure_genai, get_gemini_model, generate_gemini_content
from formatter import parse_and_format_gemini_output
from pinterest_api import create_pin

# Load environment variables
load_dotenv()

class Config:
    """Configuration constants"""
    DEFAULT_IMAGE_PATH = 'tst.jpg'
    GEMINI_MODEL_NAME = "gemini-2.5-flash-preview-05-20"
    DEFAULT_TAGS = ["bible quotes"]

def get_prompt() -> str:
    """Returns the standardized prompt for Gemini"""
    return """
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

def process_gemini_response(response: str) -> Optional[Dict]:
    """Process and validate Gemini response"""
    if not response:
        print("Error: Empty response from Gemini")
        return None
    
    formatted_data = parse_and_format_gemini_output(response)
    if not formatted_data:
        print("Error: Could not format Gemini response.")
        return None
    
    print("\n--- Formatted Response ---")
    for key, value in formatted_data.items():
        print(f"{key}: {value}")
    
    return formatted_data

def upload_to_pinterest(image_path: str, formatted_data: Dict) -> bool:
    """Handle Pinterest upload with proper validation"""
    required_fields = ["title", "description", "alt_text"]
    if not all(formatted_data.get(field) for field in required_fields):
        print("Error: Missing required fields for Pinterest upload")
        return False
    
    try:
        result = create_pin(
            board_id=os.getenv("PINTEREST_BOARD_ID"),
            image_path=Config.DEFAULT_IMAGE_PATH,
            title=formatted_data["title"],
            description=formatted_data["description"],
            alt_text=formatted_data["alt_text"],
            tags=Config.DEFAULT_TAGS,
            access_token=os.getenv("PINTEREST_ACCESS_TOKEN")
        )
        
        if result:
            print("\nPin uploaded successfully!")
            print(f"Pin ID: {result.get('id')}")
            print(f"View URL: {result.get('url', 'URL not available')}")
            return True
        return False
        
    except Exception as e:
        print(f"Pinterest upload error: {str(e)}")
        return False

def main():
    print("=== Starting Pin Creation Process ===")
    
    # --- Configuration ---
    image_path = Path(Config.DEFAULT_IMAGE_PATH)
    
    # --- Validate Inputs ---
    if not validate_image_path(image_path):
        print(f"Error: Invalid image path {image_path}")
        return
    
    api_key = validate_api_key()
    if not api_key:
        print("Error: Invalid API key")
        return
    
    # --- Initialize Gemini ---
    configure_genai(api_key)
    model = get_gemini_model(Config.GEMINI_MODEL_NAME)
    if not model:
        print(f"Error: Could not load model {Config.GEMINI_MODEL_NAME}")
        return
    
    # --- Load Image ---
    img = load_image(image_path)
    if not img:
        print(f"Error: Could not load image {image_path}")
        return
    
    # --- Generate Content ---
    prompt = get_prompt()
    gemini_response = generate_gemini_content(model, prompt, img)
    
    # --- Process Response ---
    formatted_data = process_gemini_response(gemini_response)
    if not formatted_data:
        return
    
    # --- Confidence Check ---
    if formatted_data.get("confidence_level", "low") != "high":
        print(f"Warning: confidence level ({formatted_data['confidence_level']})")
        proceed = input("Continue with upload? (y/n): ").lower() == 'y'
        if not proceed:
            return
    
    # --- Upload to Pinterest ---
    upload_to_pinterest(image_path, formatted_data)
    
    print("\n=== Process Complete ===")

if __name__ == "__main__":
    main()