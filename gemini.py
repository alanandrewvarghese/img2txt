import google.generativeai as genai

def configure_genai(api_key):
    genai.configure(api_key=api_key)

def get_gemini_model(model_name):
    try:
        model = genai.GenerativeModel(model_name)
        return model
    except Exception as e:
        print(f"Error: Could not load model '{model_name}'. Please check the model name.")
        print(f"Details: {e}")
        return None

def generate_gemini_content(model, prompt, img):
    try:
        print("\n--- Sending request to Gemini... ---")
        response = model.generate_content([prompt, img])
        print("\n--- Gemini's Response ---")
        print(response.text)
        return(response.text)
    except Exception as e:
        print(f"\nError during Gemini API call: {e}")
        print("Possible issues: API key, rate limits, or network problems.")
