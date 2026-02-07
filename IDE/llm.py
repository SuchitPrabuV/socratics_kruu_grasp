from django.conf import settings
import logging
import json
import urllib.request

logger = logging.getLogger(__name__)

LLM_PROVIDER = getattr(settings, 'LLM_PROVIDER', 'gemini').lower()

api_key = getattr(settings, 'GEMINI_API_KEY', None)
client = None
if LLM_PROVIDER == 'gemini':
    from google import genai
    from google.genai import types
    if api_key:
        client = genai.Client(api_key=api_key)

SYSTEM_PROMPT = """
You are Socratis, a wise and patient coding mentor for beginners.
Your goal is to help the student find the solution themselves using the Socratic method.

RULES:
1. NEVER provide the corrected code or the answer directly. Refuse if asked.
2. Analyze the user's code and the error message to identify the logical flaw.
3. Tell the exact name / description of the concept they are missing and error they are facing.
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

def _build_prompt(code, error, problem_description=""):
    return f"""
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


def _generate_hint_gemini(code, error, problem_description=""):
    if not client:
        return {
            "analogy": "I am currently offline (API Key missing).",
            "hint": "Please check your configuration.",
            "concept": "System Error"
        }

    prompt = _build_prompt(code, error, problem_description)
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type='application/json'
        )
    )
    return json.loads(response.text)


def _generate_hint_ollama(code, error, problem_description=""):
    prompt = _build_prompt(code, error, problem_description)
    model = getattr(settings, 'OLLAMA_MODEL', 'llama3')
    base_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
    url = f"{base_url.rstrip('/')}/api/generate"

    payload = {
        "model": model,
        "prompt": prompt,
        "format": "json",
        "stream": False
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = resp.read().decode("utf-8")
        data = json.loads(body)
        response_text = data.get("response", "")
        return json.loads(response_text)


def generate_hint(code, error, problem_description=""):
    """
    Generates a Socratic hint using the configured LLM provider.
    """
    try:
        if LLM_PROVIDER == 'ollama':
            return _generate_hint_ollama(code, error, problem_description)
        return _generate_hint_gemini(code, error, problem_description)
    except Exception as e:
        logger.error(f"LLM Error: {e}")
        return {
            "analogy": "I'm having trouble thinking clearly right now.",
            "hint": f"It seems there's a system error: {str(e)}",
            "concept": "System Error: " + str(e)
        }
