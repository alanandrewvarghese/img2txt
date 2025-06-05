import json

REQUIRED_KEYS = [
    "title",
    "extracted_bible_verse_malayalam",
    "bible_verse_english_translation",
    "alternative_text_for_main_content",
]

DEFAULT_TITLE = "Trinity Catholic Media"
DEFAULT_DESCRIPTION = (
    "Stay inspired daily! Follow our WhatsApp channel for the latest Bible verses: "
    "https://whatsapp.com/channel/0029VbAhLis0rGiVQd0HSw03"
)
WHATSAPP_LINK = (
    "\n\nStay inspired daily! Follow our WhatsApp channel for the latest Bible verses: "
    "https://whatsapp.com/channel/0029VbAhLis0rGiVQd0HSw03"
)

def clean_json_string(json_str):
    """Remove code block markers and fix common JSON issues."""
    cleaned = json_str.strip()
    
    # Remove JSON code block markers
    for marker in ['```json', '```']:
        if cleaned.startswith(marker):
            cleaned = cleaned[len(marker):]
        if cleaned.endswith(marker):
            cleaned = cleaned[:-len(marker)]
    
    cleaned = cleaned.strip()
    
    # Fix trailing commas (common Gemini issue)
    cleaned = cleaned.replace(',\n}', '\n}').replace(',\n]', '\n]')
    
    return cleaned

def parse_json_safely(json_str, original_str):
    """Attempt to parse JSON with proper error handling."""
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}\nRaw output was:\n{original_str}")
        return None

def ensure_required_fields(data):
    """Ensure all required keys exist in the data dictionary."""
    if not isinstance(data, dict):
        return {}
        
    return {key: data.get(key) for key in REQUIRED_KEYS}

def format_title(title):
    """Format the title with fallback to default."""
    if not title:
        print("Warning: Title is missing in the response.")
        return DEFAULT_TITLE
    return f"{title.strip()} | Trinity Catholic Media"

def format_description(verse_malayalam, verse_english):
    """Format the description with fallback to default."""
    if not verse_malayalam or not verse_english:
        print("Warning: Bible verse information is missing in the response.")
        return DEFAULT_DESCRIPTION
    
    return (
        f"{verse_malayalam.strip()}\n\n"
        f"English: {verse_english.strip()}"
        f"{WHATSAPP_LINK}"
    )

def format_alt_text(alt_text):
    """Format alternative text with empty string fallback."""
    if not alt_text:
        print("Warning: Alternative text is missing in the response.")
        return ""
    return alt_text.strip()

def parse_and_format_gemini_output(output_str):
    """
    Accepts a JSON string from Gemini, parses it, and returns a cleaned dict.
    Fixes common Gemini output issues (e.g., trailing commas, code block wrappers).
    
    Returns:
        dict: Formatted data with title, description, and alt_text
              or empty dict if parsing fails
    """
    if not output_str:
        return {}
    
    cleaned_str = clean_json_string(output_str)
    parsed_data = parse_json_safely(cleaned_str, output_str)
    
    if not parsed_data:
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
        }
    except Exception as e:
        print(f"Error formatting output: {e}")
        return {}