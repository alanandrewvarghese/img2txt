import requests
import os
from typing import Optional, Dict, List, Any
import json
from pydantic import BaseModel, ValidationError, field_validator, model_validator
from pathlib import Path

class PinData(BaseModel):
    """Validated data model for Pinterest pin creation."""
    board_id: str
    image_path: str
    title: str
    description: str
    alt_text: str
    tags: Optional[List[str]] = None
    access_token: str

    @field_validator('image_path')
    def validate_image_path(cls, v: str) -> str:
        """Validate that the image file exists and is readable."""
        path = Path(v)
        if not path.exists():
            raise ValueError(f"Image file not found: {v}")
        if not path.is_file():
            raise ValueError(f"Path is not a file: {v}")
        if not os.access(v, os.R_OK):
            raise ValueError(f"Cannot read image file: {v}")
        return v

    @field_validator('board_id', 'title', 'description', 'alt_text', 'access_token')
    def validate_not_empty(cls, v: str) -> str:
        """Validate that required fields are not empty."""
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()

    @model_validator(mode='after')
    def validate_tags_content(self) -> 'PinData':
        """Validate tags content if present."""
        if self.tags:
            if len(self.tags) > 20:  # Pinterest may have tag limits
                raise ValueError("Too many tags (max 20)")
            if any(not tag.strip() for tag in self.tags):
                raise ValueError("Tags cannot be empty")
        return self

def upload_pin(pin_data: PinData) -> Optional[Dict[str, Any]]:
    """
    Uploads a pin to Pinterest using the v5 API.
    
    Args:
        pin_data: Validated PinData object containing all pin information
    
    Returns:
        API response as a dictionary if successful, None otherwise.
    
    Raises:
        requests.exceptions.RequestException: For HTTP-related errors
    """
    url = "https://api.pinterest.com/v5/pins"
    headers = {
        "Authorization": f"Bearer {pin_data.access_token}",
        # Content-Type will be set automatically by requests for multipart
    }
    
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
                url,
                headers=headers,
                files=files,
                data=data,
                timeout=(3.05, 27)  # Connect and read timeouts
            )
            
            response.raise_for_status()
            return response.json()
            
    except requests.exceptions.RequestException as e:
        error_msg = f"Error uploading pin: {str(e)}"
        if e.response is not None:
            try:
                error_detail = e.response.json().get('message', e.response.text)
                error_msg += f"\nAPI Error: {error_detail}"
            except ValueError:
                error_msg += f"\nResponse: {e.response.text}"
        print(error_msg)
        return None

def create_pin(
    board_id: str,
    image_path: str,
    title: str,
    description: str,
    alt_text: str,
    tags: Optional[List[str]] = None,
    access_token: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Public interface for creating a pin with validation.
    
    Args:
        Same as individual parameters in PinData
    
    Returns:
        API response or None on failure
    """
    try:
        pin_data = PinData(
            board_id=board_id,
            image_path=image_path,
            title=title,
            description=description,
            alt_text=alt_text,
            tags=tags,
            access_token=access_token or os.getenv("PINTEREST_ACCESS_TOKEN")
        )
        return upload_pin(pin_data)
    except ValidationError as e:
        print(f"Validation error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return None

if __name__ == "__main__":
    # Example usage
    try:
        result = create_pin(
            board_id=os.getenv("PINTEREST_BOARD_ID", "<YOUR_BOARD_ID>"),
            image_path="67.jpg",
            title="Sample Pin Title",
            description="Sample description for the pin.",
            alt_text="Alternative text for accessibility.",
            tags=["bible", "malayalam", "verse"],
            access_token=os.getenv("PINTEREST_ACCESS_TOKEN")
        )
        
        if result:
            print("Pin uploaded successfully!")
            print(f"Pin ID: {result.get('id')}")
            print(f"View URL: {result.get('url', 'URL not available')}")
        else:
            print("Failed to upload pin")
            
    except Exception as e:
        print(f"Error in example usage: {str(e)}")