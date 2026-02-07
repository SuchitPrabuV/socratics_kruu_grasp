from django.conf import settings
from google import genai
from google.genai import types
import logging
import json

logger = logging.getLogger(__name__)

# Configure Gemini
api_key = getattr(settings, 'GEMINI_API_KEY', None)
client = None
if api_key:
    client = genai.Client(api_key=api_key)

SYSTEM_PROMPT = """
You are Socratis, a wise and patient coding mentor for beginners.
Your goal is to help the student find the solution themselves using the Socratic method.

RULES:
1. NEVER provide the corrected code or the answer directly. Refuse if asked.
2. Analyze the user's code and the error message to identify the logical flaw.
3. Use a simple, real-world analogy (non-technical) to explain the concept (e.g., cooking, traffic, building).
4. Ask a guiding question that leads them to the fix.
5. Be encouraging but firm about not giving the answer.
6. Keep your response concise (under 4 sentences).

FORMAT:
Return a JSON object with this structure:
{
    "analogy": "The analogy explanation...",
    "hint": "The guiding question...",
    "concept": "The core concept they are missing (e.g. Loop Termination)"
}
"""

def generate_hint(code, error, problem_description=""):
    """
    Generates a Socratic hint using the Google GenAI SDK.
    """
    try:
        if not client:
            return {
                "analogy": "I am currently offline (API Key missing).",
                "hint": "Please check your configuration.",
                "concept": "System Error"
            }

        prompt = f"""
        {SYSTEM_PROMPT}

        Problem: {problem_description}
        
        User Code:
        ```python
        {code}
        ```
        
        Error/Output:
        {error}
        
        Remember to output valid JSON only.
        """

        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json'
            )
        )
        
        return json.loads(response.text)

    except Exception as e:
        logger.error(f"LLM Error: {e}")
        return {
            "analogy": "I'm having trouble thinking clearly right now.",
            "hint": f"It seems there's a system error: {str(e)}",
            "concept": "System Error: " + str(e)
        }
