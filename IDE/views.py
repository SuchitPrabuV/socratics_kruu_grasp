from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Interaction
import json
import os
from .analysis import analyze_structure

# Placeholder for LangChain/OpenAI to avoid direct dependency if not installed yet
# In a real scenario, you would import:
# from langchain.chat_models import ChatOpenAI
# from langchain.schema import HumanMessage, SystemMessage

def workspace(request):
    return render(request, 'workspace.html')

@csrf_exempt
def get_hint(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            code = data.get('code', '')
            error_msg = data.get('error', '')
            
            # Analyze Code Structure (Still useful for providing context)
            analysis = analyze_structure(code)
            
            # Use LLM for Socratic Hint
            from .llm import generate_hint
            llm_Response = generate_hint(code, error_msg)
            
            hint_content = f"{llm_Response.get('analogy', '')} {llm_Response.get('hint', '')}"
            concept = llm_Response.get('concept', 'Logic')

            # Save Interaction
            Interaction.objects.create(
                user_code=code,
                error_log=error_msg,
                ai_hint=hint_content
            )

            return JsonResponse({
                'hint': hint_content,
                'analysis': analysis,
                'concept': concept
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


def empty_js(request):
    """
    Serve empty JS to silence 404s for source maps or helper scripts like stackframe.js
    """
    return JsonResponse({}, safe=False)
