from PIL import Image

def load_image(image_file_path):
    try:
        img = Image.open(image_file_path)
        return img
    except Exception as e:
        print(f"Error opening image: {e}")
        return None
