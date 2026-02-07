from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Interaction, ConceptMastery
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
            
            # 1. Analyze Code Structure
            analysis = analyze_structure(code)
            
            # 2. Logic for Mock Response (Socratic)
            hint_content = "I see complexity in your code logic. "
            if "NameError" in error_msg:
                hint_content = "It seems you are calling out to someone who isn't there. Imagine trying to call a friend whose name isn't in your contacts. Did you define the variable before using it?"
            elif "SyntaxError" in error_msg:
                hint_content = "The grammar of your code seems a bit off, like a sentence missing a period. Check your colons and indentation."
            elif "IndentationError" in error_msg:
                hint_content = "Python is very particular about alignment. Like soldiers needed to be in line, code blocks must be perfectly aligned."
            else:
                hint_content = f"I noticed you are using {', '.join(analysis.get('concepts_found', []))}. However, the error '{error_msg}' suggests a logical disconnect. What did you intend happen at that step?"

            # 3. Save Interaction
            Interaction.objects.create(
                user_code=code,
                error_log=error_msg,
                ai_hint=hint_content
            )

            return JsonResponse({
                'hint': hint_content,
                'analysis': analysis
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
def record_success(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            code = data.get('code', '')
            
            # Analyze what concepts are in the successful code
            # In a real "diff" scenario, we would compare with Interaction.objects.last().user_code
            # Here we simplify: if the code works and contains a concept -> XP boost
            analysis = analyze_structure(code)
            concepts = analysis.get('concepts_found', [])
            
            # Base XP
            xp_gained = {}
            
            # Granular Update
            for concept in concepts:
                # e.g., 'loops' -> 'Loop Logic', 'conditionals' -> 'Branching'
                obj, created = ConceptMastery.objects.get_or_create(concept=concept)
                
                # Check history to see if this is "progress" (simplistic simulation of diff-check)
                # If they struggled with this concept recently, give more XP?
                # For now, standard increment
                increment = 50
                obj.score += increment
                obj.save()
                
                xp_gained[concept] = obj.score

            # Get total score and breakdown
            mastery = list(ConceptMastery.objects.values('concept', 'score'))
            total_score = sum([item['score'] for item in mastery])
            
            return JsonResponse({
                'status': 'success', 
                'new_score': total_score,
                'breakdown': mastery, 
                'gained': xp_gained
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid method'}, status=400)

def get_progress(request):
    # API to fetch current mastery status
    mastery = list(ConceptMastery.objects.values('concept', 'score'))
    total_score = sum([item['score'] for item in mastery])
    return JsonResponse({'mastery': mastery, 'total_score': total_score})

def empty_js(request):
    """
    Serve empty JS to silence 404s for source maps or helper scripts like stackframe.js
    """
    return JsonResponse({}, safe=False)
