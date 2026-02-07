from django.conf import settings
import logging
import json
import urllib3

logger = logging.getLogger(__name__)

LLM_PROVIDER = getattr(settings, 'LLM_PROVIDER', 'groq').lower()

# Client Initialization
client_gemini = None
client_groq = None

# Initialize Gemini if needed
if LLM_PROVIDER == 'gemini':
    try:
        from google import genai
        from google.genai import types
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if api_key:
            client_gemini = genai.Client(api_key=api_key)
    except ImportError:
        logger.warning("google-genai library not installed.")

# Initialize Groq if needed
if LLM_PROVIDER == 'groq':
    try:
        from groq import Groq
        api_key_groq = getattr(settings, 'GROQ_API_KEY', None)
        if api_key_groq:
            client_groq = Groq(api_key=api_key_groq)
    except ImportError:
        logger.warning("groq library not installed.")

SYSTEM_PROMPT = """
You are Socratis, a wise and patient coding mentor for beginners.
You teach using the Socratic method and never give direct answers.
The student is coding in Python.

RULES:
1. NEVER provide corrected code or full solutions.
2. Carefully analyze the student's code and error message.
3. Identify the exact missing concept and real error type.
4. If a specific line is the cause, identify its line number (integer).
5. Ask one guiding question that leads the student toward fixing the issue but it should be short.
6. Be encouraging, precise, and concise (max 3 sentences total).
7. Give the output clearly

FORMAT:
Respond ONLY in valid JSON:

{
  "analogy": "Simple real-life analogy for the mistake",
  "hint": "One guiding question to help them think",
  "concept": "Exact programming concept (e.g., Function Scope, Syntax Error)",
  "line_no": 0
}

Note: `line_no` should be the integer line number of the error, or 0 if general/unknown.
Do not include anything outside this JSON.
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
    if not client_gemini:
        return {
            "analogy": "I am currently offline (API Key missing).",
            "hint": "Please check your configuration.",
            "concept": "System Error"
        }

    prompt = _build_prompt(code, error, problem_description)
    response = client_gemini.models.generate_content(
        model='gemini-2.0-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type='application/json'
        )
    )
    return json.loads(response.text)


def _generate_hint_ollama(code, error, problem_description=""):
    import urllib3
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

    http = urllib3.PoolManager(timeout=30.0)
    try:
        response = http.request(
            'POST', 
            url,
            body=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status != 200:
            error_body = response.data.decode('utf-8')
            logger.error(f"Ollama Error {response.status}: {error_body}")
            raise Exception(f"Ollama returned {response.status}: {error_body}")

        body = response.data.decode("utf-8")
        data = json.loads(body)
        response_text = data.get("response", "")
        return json.loads(response_text)
        
    except Exception as e:
        logger.error(f"Ollama Connection Error: {e}")
        raise e

def _generate_hint_groq(code, error, problem_description=""):
    if not client_groq:
        return {
            "analogy": "I am currently offline (Groq API Key missing).",
            "hint": "Please check your configuration.",
            "concept": "System Error"
        }
        
    prompt = _build_prompt(code, error, problem_description)
    
    try:
        completion = client_groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1024,
            top_p=1,
            stream=False,
            response_format={"type": "json_object"}
        )
        
        content = completion.choices[0].message.content
        return json.loads(content)
        
    except Exception as e:
        logger.error(f"Groq API Error: {e}")
        raise e


def generate_hint(code, error, problem_description=""):
    """
    Generates a Socratic hint using the configured LLM provider.
    """
    try:
        if LLM_PROVIDER == 'ollama':
            return _generate_hint_ollama(code, error, problem_description)
        elif LLM_PROVIDER == 'groq':
            return _generate_hint_groq(code, error, problem_description)
        else: # Default to gemini
             return _generate_hint_gemini(code, error, problem_description)

    except Exception as e:
        logger.error(f"LLM Error: {e}")
        return {
            "analogy": "I'm having trouble thinking clearly right now.",
            "hint": f"It seems there's a system error: {str(e)}",
            "concept": "System Error: " + str(e)
        }
