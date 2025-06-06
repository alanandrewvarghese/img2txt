import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

import google.generativeai as genai
import requests
from dotenv import load_dotenv
from PIL import Image
from pydantic import BaseModel, ValidationError, field_validator, model_validator

# --- Constants ---
DEFAULT_TITLE = "Trinity Catholic Media"
DEFAULT_DESCRIPTION = (
    "Stay inspired daily! Follow our WhatsApp channel for the latest Bible verses: "
    "https://whatsapp.com/channel/0029VbAhLis0rGiVQd0HSw03"
)
WHATSAPP_LINK = (
    "\n\nStay inspired daily! Follow our WhatsApp channel for the latest Bible verses: "
    "https://whatsapp.com/channel/0029VbAhLis0rGiVQd0HSw03"
)
REQUIRED_KEYS = [
    "title",
    "extracted_bible_verse_malayalam",
    "bible_verse_english_translation",
    "alternative_text_for_main_content",
    "confidence_level",
]


class Config:
    DEFAULT_IMAGE_PATH = "tst.jpg"
    GEMINI_MODEL_NAME = "gemini-2.5-flash-preview-05-20"
    DEFAULT_TAGS = ["bible quotes"]


# --- Validators ---
def validate_image_path(image_path: Path) -> bool:
    """Validate that the image file exists and is accessible."""
    if not image_path.exists():
        print(f"Error: Image file not found at '{image_path}'")
        print("Please update 'image_file_path' or ensure the image is in the same directory.")
        return False
    return True


def validate_api_key() -> Optional[str]:
    """Validate and return the Gemini API key from environment variables."""
    if api_key := os.environ.get("GEMINI_API_KEY"):
        return api_key
    
    print("Error: GEMINI_API_KEY environment variable not set.")
    print("Please obtain your Gemini API key from Google AI Studio (https://aistudio.google.com/app/apikey)")
    print("Example: export GEMINI_API_KEY='your_api_key_here'")
    return None


# --- Image Loader ---
def load_image(image_path: Path) -> Optional[Image.Image]:
    """Load an image from the given path."""
    try:
        return Image.open(image_path)
    except Exception as e:
        print(f"Error opening image: {e}")
        return None


# --- Gemini API ---
def configure_genai(api_key: str) -> None:
    """Configure the Gemini API with the provided key."""
    genai.configure(api_key=api_key)


def get_gemini_model(model_name: str) -> Optional[genai.GenerativeModel]:
    """Initialize and return a Gemini model instance."""
    try:
        return genai.GenerativeModel(model_name)
    except Exception as e:
        print(f"Error: Could not load model '{model_name}'. Please check the model name.")
        print(f"Details: {e}")
        return None


def generate_gemini_content(
    model: genai.GenerativeModel, 
    prompt: str, 
    image: Image.Image
) -> Optional[str]:
    """Generate content from Gemini using the given prompt and image."""
    try:
        print("\n--- Sending request to Gemini... ---")
        response = model.generate_content([prompt, image])
        print("\n--- Gemini's Response ---")
        print(response.text)
        return response.text
    except Exception as e:
        print(f"\nError during Gemini API call: {e}")
        print("Possible issues: API key, rate limits, or network problems.")
        return None


# --- Formatter ---
def clean_json_string(json_str: str) -> str:
    """Clean and prepare a JSON string for parsing."""
    cleaned = json_str.strip()
    for marker in ["```json", "```"]:
        if cleaned.startswith(marker):
            cleaned = cleaned[len(marker):]
        if cleaned.endswith(marker):
            cleaned = cleaned[:-len(marker)]
    cleaned = cleaned.strip()
    cleaned = cleaned.replace(",\n}", "\n}").replace(",\n]", "\n]")
    return cleaned


def parse_json_safely(json_str: str, original_str: str) -> Optional[Dict[str, Any]]:
    """Safely parse a JSON string with error handling."""
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}\nRaw output was:\n{original_str}")
        return None


def ensure_required_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure all required fields are present in the data dictionary."""
    return {key: data.get(key) for key in REQUIRED_KEYS} if isinstance(data, dict) else {}


def format_title(title: Optional[str]) -> str:
    """Format the title with fallback to default if missing."""
    return f"{title.strip()} | Trinity Catholic Media" if title else DEFAULT_TITLE


def format_description(verse_malayalam: Optional[str], verse_english: Optional[str]) -> str:
    """Format the description with fallback to default if missing."""
    if not verse_malayalam or not verse_english:
        print("Warning: Bible verse information is missing in the response.")
        return DEFAULT_DESCRIPTION
    return f"{verse_malayalam.strip()}\n\nEnglish: {verse_english.strip()}{WHATSAPP_LINK}"


def format_alt_text(alt_text: Optional[str]) -> str:
    """Format the alt text with empty string fallback."""
    return alt_text.strip() if alt_text else ""


def parse_and_format_gemini_output(output_str: str) -> Dict[str, Any]:
    """Parse and format Gemini's output into a structured dictionary."""
    if not output_str:
        return {}
    
    cleaned_str = clean_json_string(output_str)
    if not (parsed_data := parse_json_safely(cleaned_str, output_str)):
        return {}
    
    data = ensure_required_fields(parsed_data)
    try:
        return {
            "title": format_title(data.get("title")),
            "description": format_description(
                data.get("extracted_bible_verse_malayalam"),
                data.get("bible_verse_english_translation")
            ),
            "alt_text": format_alt_text(data.get("alternative_text_for_main_content")),
            "confidence_level": data.get("confidence_level", "low").lower(),
        }
    except Exception as e:
        print(f"Error formatting output: {e}")
        return {}


# --- Pinterest API with Pydantic ---
class PinData(BaseModel):
    """Pydantic model for Pinterest pin data validation."""
    board_id: str
    image_path: str
    title: str
    description: str
    alt_text: str
    tags: Optional[List[str]] = None
    access_token: str

    @field_validator("image_path")
    def validate_image_path(cls, v: str) -> str:
        """Validate that the image path exists and is readable."""
        path = Path(v)
        if not path.exists():
            raise ValueError(f"Image file not found: {v}")
        if not path.is_file():
            raise ValueError(f"Path is not a file: {v}")
        if not os.access(v, os.R_OK):
            raise ValueError(f"Cannot read image file: {v}")
        return v

    @field_validator("board_id", "title", "description", "alt_text", "access_token")
    def validate_not_empty(cls, v: str) -> str:
        """Validate that required fields are not empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

    @model_validator(mode="after")
    def validate_tags_content(self) -> "PinData":
        """Validate tags content if present."""
        if self.tags:
            if len(self.tags) > 20:
                raise ValueError("Too many tags (max 20)")
            if any(not tag.strip() for tag in self.tags):
                raise ValueError("Tags cannot be empty strings")
        return self


def upload_pin(pin_data: PinData) -> Optional[Dict[str, Any]]:
    """Upload a pin to Pinterest using the provided data."""
    url = "https://api.pinterest.com/v5/pins"
    headers = {"Authorization": f"Bearer {pin_data.access_token}"}

    try:
        with open(pin_data.image_path, "rb") as image_file:
            files = {"image": image_file}
            data = {
                "board_id": pin_data.board_id,
                "title": pin_data.title,
                "description": pin_data.description,
                "alt_text": pin_data.alt_text,
            }
            if pin_data.tags:
                data["tags"] = json.dumps([tag.strip() for tag in pin_data.tags])

            response = requests.post(
                url, headers=headers, files=files, data=data, timeout=(3.05, 27)
            )
            response.raise_for_status()
            return response.json()
    except requests.exceptions.RequestException as e:
        error_msg = f"Error uploading pin: {str(e)}"
        if e.response is not None:
            try:
                error_detail = e.response.json().get("message", e.response.text)
                print(f"API Response: {error_detail}")
            except ValueError:
                print(f"API Response: {e.response.text}")
        print(error_msg)
        return None


def create_pin(
    board_id: str,
    image_path: str,
    title: str,
    description: str,
    alt_text: str,
    tags: Optional[List[str]] = None,
    access_token: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Create and upload a pin to Pinterest with validation."""
    try:
        pin_data = PinData(
            board_id=board_id,
            image_path=image_path,
            title=title,
            description=description,
            alt_text=alt_text,
            tags=tags,
            access_token=access_token or os.getenv("PINTEREST_ACCESS_TOKEN"),
        )
        return upload_pin(pin_data)
    except ValidationError as e:
        print(f"Validation error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return None


# --- Main Workflow ---
def get_prompt() -> str:
    """Return the standardized prompt for Gemini."""
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


def process_gemini_response(response: str) -> Optional[Dict[str, Any]]:
    """Process and format Gemini's response."""
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


def upload_to_pinterest(image_path: str, formatted_data: Dict[str, Any]) -> bool:
    """Upload formatted data to Pinterest using direct base64 image upload."""
    required_fields = ["title", "description", "alt_text"]
    if not all(formatted_data.get(field) for field in required_fields):
        print("Error: Missing required fields for Pinterest upload")
        return False

    access_token = os.getenv("PINTEREST_ACCESS_TOKEN")
    board_id = os.getenv("PINTEREST_BOARD_ID")
    title = formatted_data["title"]
    description = formatted_data["description"]
    alt_text = formatted_data["alt_text"]
    link = os.getenv("WHATSAPP_LINK", "https://whatsapp.com/channel/0029VbAhLis0rGiVQd0HSw03")

    # Read and encode the image file as base64
    try:
        with open(image_path, "rb") as img_file:
            import base64
            image_base64 = base64.b64encode(img_file.read()).decode("utf-8")
    except Exception as e:
        print(f"Error reading image for base64 upload: {e}")
        return False

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    payload = {
        'board_id': board_id,
        'media_source': {
            'source_type': 'image_base64',
            'content_type': 'image/jpeg',  # Change if not JPEG
            'data': image_base64,
        },
        'title': title,
        'description': description,
        'link': link,
        'alt_text': alt_text,
    }
    try:
        response = requests.post(
            'https://api.pinterest.com/v5/pins',
            headers=headers,
            data=json.dumps(payload)
        )
        if response.ok:
            print('Pin created successfully!')
            print(json.dumps(response.json(), indent=2))
            return True
        else:
            print('Failed to create pin:')
            print(response.status_code, response.text)
            return False
    except Exception as e:
        print(f"Pinterest upload error: {str(e)}")
        return False


def main() -> None:
    """Main workflow execution."""
    print("=== Starting Pin Creation Process ===")
    
    image_path = Path(Config.DEFAULT_IMAGE_PATH)
    if not validate_image_path(image_path):
        return

    if not (api_key := validate_api_key()):
        return

    configure_genai(api_key)
    if not (model := get_gemini_model(Config.GEMINI_MODEL_NAME)):
        return

    if not (img := load_image(image_path)):
        return

    prompt = get_prompt()
    if not (gemini_response := generate_gemini_content(model, prompt, img)):
        return

    if not (formatted_data := process_gemini_response(gemini_response)):
        return

    if formatted_data.get("confidence_level", "low") != "high":
        print(f"Warning: confidence level ({formatted_data['confidence_level']})")
        if input("Continue with upload? (y/n): ").lower() != "y":
            return

    upload_to_pinterest(str(image_path), formatted_data)
    print("\n=== Process Complete ===")


if __name__ == "__main__":
    load_dotenv()
    main()