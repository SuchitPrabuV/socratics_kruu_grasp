from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Interaction, StudentSession
from django.utils import timezone
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
            session_id = data.get('session_id', 'default')
            
            # Analyze Code Structure (Still useful for providing context)
            analysis = analyze_structure(code)
            
            # Use LLM for Socratic Hint
            from .llm import generate_hint
            llm_Response = generate_hint(code, error_msg)
            
            hint_content = f"{llm_Response.get('analogy', '')} {llm_Response.get('hint', '')}"
            concept = llm_Response.get('concept', 'Logic')

            # Save Interaction with session_id
            Interaction.objects.create(
                user_code=code,
                error_log=error_msg,
                ai_hint=hint_content,
                session_id=session_id
            )

            return JsonResponse({
                'hint': llm_Response.get('hint', ''),
                'analogy': llm_Response.get('analogy', ''),
                'analysis': analysis,
                'concept': concept,
                'line_no': llm_Response.get('line_no', 0)
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def record_success(request):
    """Records when a student successfully fixes an error after getting a hint"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            session_id = data.get('session_id', 'default')
            
            # Get or create session
            session, created = StudentSession.objects.get_or_create(
                session_id=session_id,
                defaults={'total_score': 0, 'problems_solved': 0}
            )
            
            # Find the last unresolved interaction for this session
            last_interaction = Interaction.objects.filter(
                session_id=session_id,
                was_resolved=False,
                error_log__isnull=False
            ).exclude(error_log='').order_by('-timestamp').first()
            
            if last_interaction:
                # Mark as resolved
                last_interaction.was_resolved = True
                last_interaction.resolved_at = timezone.now()
                last_interaction.save()
                
                # Increase score
                score_gained = 5
                session.total_score += score_gained
                session.problems_solved += 1
                session.save()
                
                return JsonResponse({
                    'success': True,
                    'new_score': session.total_score,
                    'score_gained': score_gained
                })
            
            return JsonResponse({
                'success': False, 
                'message': 'No unresolved error found'
            })
        
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


def get_score(request):
    """Get current session score"""
    session_id = request.GET.get('session_id', 'default')
    session = StudentSession.objects.filter(session_id=session_id).first()
    
    if session:
        return JsonResponse({
            'score': session.total_score,
            'problems_solved': session.problems_solved
        })
    return JsonResponse({'score': 0, 'problems_solved': 0})


def empty_js(request):
    """
    Serve empty JS to silence 404s for source maps or helper scripts like stackframe.js
    """
    return JsonResponse({}, safe=False)
