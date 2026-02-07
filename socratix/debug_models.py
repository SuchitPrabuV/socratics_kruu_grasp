import os
import django
from django.conf import settings
from google import genai

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socratics.settings')
django.setup()

def list_models():
    try:
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            print("Error: GEMINI_API_KEY not found in settings.")
            return

        client = genai.Client(api_key=api_key)
        
        print(f"Checking models with key: {api_key[:5]}...")
        
        # Pager for list_models
        # Note: In the new SDK, it might be client.models.list()
        # Let's try to iterate
        
        try:
            from google.genai import types
            pager = client.models.list(config=types.ListModelsConfig(page_size=10))
            with open('models.txt', 'w') as f:
                for m in pager:
                    f.write(f"{m.name}\n")
            print("Models written to models.txt")
        except Exception as e:
            print(f"Error listing models: {e}")

    except Exception as e:
        print(f"Critical Error: {e}")

if __name__ == "__main__":
    list_models()
