# filepath: c:\Users\alana\Desktop\imgtotxt\streamlit.py
import streamlit as st
import os
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image
import google.generativeai as genai
import json
import requests
import base64

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
    if not image_path.exists():
        st.error(f"Image file not found at '{image_path}'")
        return False
    return True

def validate_api_key(api_key: str) -> bool:
    if not api_key:
        st.error("GEMINI_API_KEY is required.")
        return False
    return True

# --- Image Loader ---
def load_image(image_path: Path) -> Image.Image:
    try:
        return Image.open(image_path)
    except Exception as e:
        st.error(f"Error opening image: {e}")
        return None

# --- Gemini API ---
def configure_genai(api_key: str) -> None:
    genai.configure(api_key=api_key)

def get_gemini_model(model_name: str):
    try:
        return genai.GenerativeModel(model_name)
    except Exception as e:
        st.error(f"Error: Could not load model '{model_name}'. Details: {e}")
        return None

def generate_gemini_content(model, prompt: str, image: Image.Image):
    try:
        response = model.generate_content([prompt, image])
        return response.text
    except Exception as e:
        st.error(f"Error during Gemini API call: {e}")
        return None

# --- Formatter ---
def clean_json_string(json_str: str) -> str:
    cleaned = json_str.strip()
    for marker in ["```json", "```"]:
        if cleaned.startswith(marker):
            cleaned = cleaned[len(marker):]
        if cleaned.endswith(marker):
            cleaned = cleaned[:-len(marker)]
    cleaned = cleaned.strip()
    cleaned = cleaned.replace(",\n}", "\n}").replace(",\n]", "\n]")
    return cleaned

def parse_json_safely(json_str: str, original_str: str):
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        st.error(f"Error parsing JSON: {e}\nRaw output was:\n{original_str}")
        return None

def ensure_required_fields(data):
    return {key: data.get(key) for key in REQUIRED_KEYS} if isinstance(data, dict) else {}

def format_title(title):
    return f"{title.strip()} | Trinity Catholic Media" if title else DEFAULT_TITLE

def format_description(verse_malayalam, verse_english):
    if not verse_malayalam or not verse_english:
        st.warning("Bible verse information is missing in the response.")
        return DEFAULT_DESCRIPTION
    return f"{verse_malayalam.strip()}\n\nEnglish: {verse_english.strip()}" + WHATSAPP_LINK

def format_alt_text(alt_text):
    return alt_text.strip() if alt_text else ""

def parse_and_format_gemini_output(output_str: str):
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
            "confidence_level": data.get("confidence_level", "low").lower(),
        }
    except Exception as e:
        st.error(f"Error formatting output: {e}")
        return {}

# --- Pinterest Upload ---
def upload_to_pinterest(image_path: str, formatted_data: dict, access_token: str, board_id: str) -> bool:
    required_fields = ["title", "description", "alt_text"]
    if not all(formatted_data.get(field) for field in required_fields):
        st.error("Missing required fields for Pinterest upload")
        return False
    link = os.getenv("WHATSAPP_LINK", "https://whatsapp.com/channel/0029VbAhLis0rGiVQd0HSw03")
    try:
        with open(image_path, "rb") as img_file:
            image_base64 = base64.b64encode(img_file.read()).decode("utf-8")
    except Exception as e:
        st.error(f"Error reading image for base64 upload: {e}")
        return False
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    payload = {
        'board_id': board_id,
        'media_source': {
            'source_type': 'image_base64',
            'content_type': 'image/jpeg',
            'data': image_base64,
        },
        'title': formatted_data["title"],
        'description': formatted_data["description"],
        'link': link,
        'alt_text': formatted_data["alt_text"],
    }
    try:
        response = requests.post(
            'https://api.pinterest.com/v5/pins',
            headers=headers,
            data=json.dumps(payload)
        )
        if response.ok:
            st.success('Pin created successfully!')
            st.json(response.json())
            return True
        else:
            st.error(f'Failed to create pin: {response.status_code} {response.text}')
            return False
    except Exception as e:
        st.error(f"Pinterest upload error: {str(e)}")
        return False

# --- Streamlit UI ---
def main():
    # Page configuration
    st.set_page_config(
        page_title="Trinity Catholic Media - Bible Verse to Pinterest",
        page_icon="📖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📖 Trinity Catholic Media</h1>
        <h3>Bible Verse Image to Pinterest Pin Converter</h3>
        <p>Transform Malayalam Bible verse images into beautiful Pinterest pins</p>
    </div>
    """, unsafe_allow_html=True)
    load_dotenv()
    
    # Sidebar for configuration
    with st.sidebar:
        st.markdown("### 🔑 Configuration")
        
        # API Keys section
        st.markdown("#### 🔐 API Credentials")
        api_key = st.text_input(
            "Gemini API Key", 
            value=os.getenv("GEMINI_API_KEY", ""), 
            type="password",
            help="Your Google Gemini API key for text extraction"
        )
        pinterest_token = st.text_input(
            "Pinterest Access Token", 
            value=os.getenv("PINTEREST_ACCESS_TOKEN", ""), 
            type="password",
            help="Your Pinterest API access token"
        )
        board_id = st.text_input(
            "Pinterest Board ID", 
            value=os.getenv("PINTEREST_BOARD_ID", ""),
            help="The ID of the Pinterest board to post to"
        )    # Main content in columns
    col1, col2 = st.columns([1, 2], gap="large")

    with col1:
        # File upload section
        st.markdown("### 📁 Upload Image")
        uploaded_file = st.file_uploader(
            "Choose an image file",
            type=["jpg", "jpeg", "png"],
            help="Upload an image containing Malayalam Bible verse text"
        )        # Image preview in col1 (small) - split into sub-columns
        image = None
        image_path = None

        if uploaded_file:
            image = Image.open(uploaded_file)
            # Save to disk for processing
            image_path = Path("uploaded_image.jpg")
            image.save(image_path)
              # Create sub-columns within col1
            preview_col, info_col = st.columns([1, 1])
            
            with preview_col:
                st.markdown("### 🖼️ Preview")
                st.image(image, caption="Uploaded Image", width=80)
            
            with info_col:
                st.markdown("### ℹ️ Details")
                st.write(f"**Format:** {image.format}")
                st.write(f"**Size:** {image.size[0]} x {image.size[1]}")
                # Add file size info
                file_size = len(uploaded_file.getvalue()) / 1024  # KB
                if file_size > 1024:
                    st.write(f"**File Size:** {file_size/1024:.1f} MB")
                else:
                    st.write(f"**File Size:** {file_size:.1f} KB")
            
            # Process button under the sub-columns, full width of col1
            st.markdown("---")
            if st.button("🚀 Process Image with AI", key="main_process", type="primary", use_container_width=True):
                if not validate_api_key(api_key):
                    st.error("⚠️ Please enter a valid Gemini API key.")
                # elif not pinterest_token or not board_id:
                #     st.error("⚠️ Please enter Pinterest credentials.")
                elif not image_path or not validate_image_path(image_path):
                    st.error("⚠️ Image not available for processing.")
                else:
                    # Processing workflow with progress bar
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    try:
                        # Step 1: Configure Gemini
                        status_text.text("🔧 Configuring Gemini AI...")
                        progress_bar.progress(20)
                        configure_genai(api_key)
                        
                        # Step 2: Load model
                        status_text.text("🤖 Loading AI model...")
                        progress_bar.progress(40)
                        model = get_gemini_model(Config.GEMINI_MODEL_NAME)
                        if not model:
                            st.error("❌ Failed to load AI model.")
                            st.stop()

                        # Step 3: Prepare image
                        status_text.text("🖼️ Preparing image...")
                        progress_bar.progress(60)
                        img_for_gemini = load_image(image_path)
                        if not img_for_gemini:
                            st.error("❌ Failed to load image.")
                            st.stop()

                        # Step 4: Generate content
                        status_text.text("🧠 Analyzing image with AI...")
                        progress_bar.progress(80)
                        
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
                        
                        # Custom spinner for Gemini call
                        with st.spinner("🤖 AI is analyzing your image..."):
                            response = model.generate_content([prompt, img_for_gemini])
                        
                        progress_bar.progress(90)
                        status_text.text("📝 Processing results...")
                        
                        # Display raw response in expander
                        with st.expander("🔍 View Raw AI Response"):
                            st.code(response.text, language="json")

                        # Step 5: Format response
                        formatted_data = parse_and_format_gemini_output(response.text)
                        if not formatted_data:
                            st.error("❌ Could not format AI response.")
                            st.stop()

                        progress_bar.progress(100)
                        status_text.text("✅ Processing complete!")
                        
                        # Store in session state
                        st.session_state.processed_data = formatted_data
                        st.session_state.processing_complete = True
                          # Clear progress indicators
                        progress_bar.empty()
                        status_text.empty()
                        
                    except Exception as e:
                        st.error(f"❌ An error occurred during processing: {str(e)}")
                        progress_bar.empty()
                        status_text.empty()

    with col2:
        st.markdown("### 📊 Results")
        if not uploaded_file:
            st.info("📤 Upload an image to see results here.")    # Initialize session state for better UX
    if 'processed_data' not in st.session_state:
        st.session_state.processed_data = None
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    if 'data_edited' not in st.session_state:
        st.session_state.data_edited = False

    # Display results if processing is complete
    if st.session_state.processing_complete and st.session_state.processed_data:
        with col2:
            # st.markdown("### 📊 Extracted Information")
              # Create tabs for better organization
            tab1, tab2, tab3 = st.tabs(["📝 Content", "🎯 Pinterest Data", "📋 Summary"])
            
            with tab1:
                data = st.session_state.processed_data
                
                subcol1, subcol2 = st.columns(2)
                with subcol1:
                    st.markdown("**📖 Malayalam Verse:**")
                    malayalam_text = data.get('description', '').split('\n\nEnglish:')[0] if 'English:' in data.get('description', '') else "Not extracted"
                    st.write(malayalam_text)
                    
                with subcol2:
                    st.markdown("**🔤 English Translation:**")
                    english_text = data.get('description', '').split('English: ')[1].split('\n\n')[0] if 'English: ' in data.get('description', '') else "Not available"
                    st.write(english_text)
                
                st.markdown("**📄 Alt Text:**")
                st.write(data.get('alt_text', 'Not available'))
            
            with tab2:
                st.markdown("### ✏️ Edit Pinterest Data")
                st.markdown("*You can modify the data below before uploading to Pinterest*")
                
                # Get current data
                data = st.session_state.processed_data
                
                # Editable fields
                with st.form("pinterest_data_form"):
                    st.markdown("#### 📝 Pinterest Pin Details")
                    
                    # Title field
                    edited_title = st.text_input(
                        "📋 Title:",
                        value=data.get('title', ''),
                        help="This will be the title of your Pinterest pin"
                    )
                    
                    # Description field
                    edited_description = st.text_area(
                        "📄 Description:",
                        value=data.get('description', ''),
                        height=200,
                        help="This will be the description of your Pinterest pin"
                    )
                    
                    # Alt text field
                    edited_alt_text = st.text_area(
                        "🔍 Alt Text:",
                        value=data.get('alt_text', ''),
                        height=80,
                        help="Alternative text for accessibility"
                    )
                    
                    # Confidence level (read-only display)
                    confidence = data.get('confidence_level', 'low')
                    st.markdown(f"**🎯 AI Confidence Level:** `{confidence.upper()}`")
                      # Form submit button
                    col1_form, col2_form = st.columns([1, 1])
                    
                    with col1_form:
                        if st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True):
                            # Update session state with edited data
                            st.session_state.processed_data.update({
                                'title': edited_title,
                                'description': edited_description,
                                'alt_text': edited_alt_text
                            })
                            st.session_state.data_edited = True
                            st.success("✅ Changes saved successfully!")
                            st.rerun()
                    
                    with col2_form:
                        if st.form_submit_button("🔄 Reset to Original", type="secondary", use_container_width=True):
                            st.info("💡 To reset, please reprocess the image.")
                  # Show raw JSON data in an expander
                with st.expander("🔍 View Raw JSON Data"):
                    st.json(st.session_state.processed_data)
            
            with tab3:
                confidence = st.session_state.processed_data.get("confidence_level", "low")
                
                # Show if data has been edited
                st.markdown("### 📊 Upload Summary")
                
                # Data validation check
                data = st.session_state.processed_data
                title_valid = bool(data.get('title', '').strip())
                desc_valid = bool(data.get('description', '').strip())
                alt_valid = bool(data.get('alt_text', '').strip())
                
                col1_summary, col2_summary = st.columns([1, 1])
                
                with col1_summary:
                    st.markdown("#### ✅ Data Validation")
                    st.write(f"📋 Title: {'✅' if title_valid else '❌'} {'Valid' if title_valid else 'Missing/Empty'}")
                    st.write(f"📄 Description: {'✅' if desc_valid else '❌'} {'Valid' if desc_valid else 'Missing/Empty'}")
                    st.write(f"🔍 Alt Text: {'✅' if alt_valid else '❌'} {'Valid' if alt_valid else 'Missing/Empty'}")
                
                with col2_summary:
                    st.markdown("#### 🎯 AI Analysis")
                    # Confidence indicator
                    if confidence == "high":
                        st.success("🎯 High Confidence - Ready to upload!")
                    elif confidence == "medium":
                        st.warning("⚠️ Medium Confidence - Please review before uploading")
                    else:
                        st.error("❗ Low Confidence - Consider using a different image")
                
                # Instructions
                st.markdown("---")
                st.info("💡 **Tip:** You can edit the Pinterest data in the '🎯 Pinterest Data' tab before uploading.")
                
                # Upload button with validation
                all_data_valid = title_valid and desc_valid and alt_valid
                
                if confidence in ["high", "medium"] and all_data_valid:
                    if st.button("📌 Upload to Pinterest", key="upload_pinterest", type="primary", use_container_width=True):
                        if not pinterest_token or not board_id:
                            st.error("⚠️ Please enter Pinterest credentials in the sidebar.")
                        else:
                            with st.spinner("📤 Uploading to Pinterest..."):
                                success = upload_to_pinterest(
                                    str(image_path), 
                                    st.session_state.processed_data, 
                                    pinterest_token, 
                                    board_id
                                )
                            
                            if success:
                                st.balloons()
                                st.success("🎉 Successfully posted to Pinterest!")
                                # Reset session state after successful upload
                                st.session_state.processed_data = None
                                st.session_state.processing_complete = False
                elif not all_data_valid:
                    st.error("❌ Upload disabled: Please ensure all Pinterest data fields are filled.")
                    st.info("💡 Go to the '🎯 Pinterest Data' tab to complete missing information.")
                else:
                    st.warning("⚠️ Upload disabled due to low confidence. Try with a clearer image or edit the data manually.")

if __name__ == "__main__":
    main()
