
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Interaction, StudentSession, ConceptMastery
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
import json
import os
from .analysis import analyze_structure

# Placeholder for LangChain/OpenAI to avoid direct dependency if not installed yet
# In a real scenario, you would import:
# from langchain.chat_models import ChatOpenAI
# from langchain.schema import HumanMessage, SystemMessage

def workspace(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'workspace.html')


# --- Authentication Views ---
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', {'error': 'Username already exists'})
        user = User.objects.create_user(username=username, password=password)
        login(request, user)
        return redirect('dashboard')
    return render(request, 'register.html')

@login_required
def dashboard(request):
    # Show all previous code and achievements for the logged-in user
    user = request.user
    # Show all code submitted by this user (session_id=username)
    interactions = Interaction.objects.filter(session_id=user.username).order_by('-timestamp')
    achievements = ConceptMastery.objects.filter(user=user)
    
    # Get total score for the user's session
    session, _ = StudentSession.objects.get_or_create(session_id=user.username)
    total_score = session.total_score
    
    return render(request, 'dashboard.html', {
        'interactions': interactions, 
        'achievements': achievements,
        'total_score': total_score
    })

@csrf_exempt
def get_hint(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            code = data.get('code', '')
            error_msg = data.get('error', '')
            session_id = data.get('session_id', 'default')
            concept = None
            
            # Analyze Code Structure (Still useful for providing context)
            analysis = analyze_structure(code)
            

            # Use LLM for Socratic Hint
            from .llm import generate_hint
            llm_Response = generate_hint(code, error_msg)
            
            hint_content = f"{llm_Response.get('analogy', '')} {llm_Response.get('hint', '')}"
            concept = llm_Response.get('concept', 'Logic')


            # Save Interaction with session_id
            user = request.user if request.user.is_authenticated else None
            Interaction.objects.create(
                user=user,
                user_code=code,
                error_log=error_msg,
                ai_hint=hint_content,
                session_id=session_id,
                concept=concept
            )


            return JsonResponse({
                'hint': llm_Response.get('hint', ''),
                'analogy': llm_Response.get('analogy', ''),
                'analysis': analysis,
                'concept': concept,
                'line_no': llm_Response.get('line_no', 0)
            })

        except Exception as e:
            raise e

    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def record_success(request):
    """Records when a student successfully fixes an error after getting a hint"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            session_id = data.get('session_id', 'default')
            concept = data.get('concept', None)
            
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

                # Concept Mastery Achievement
                user = None
                if request.user.is_authenticated:
                    user = request.user
                # If not authenticated, we can't save ConceptMastery linked to a user account
                # but we can track session score (already handled above)

                
                mastery_given = False
                has_mastery = False
                MIN_RESOLVED_FOR_BADGE = 3
                
                if user and concept:
                    # Check if already mastered
                    has_mastery = ConceptMastery.objects.filter(user=user, concept=concept).exists()
                    
                    # Check how many times this concept has been resolved
                    resolved_count = Interaction.objects.filter(
                        user=user, 
                        concept=concept, 
                        was_resolved=True
                    ).count()
                    
                    if resolved_count >= MIN_RESOLVED_FOR_BADGE and not has_mastery:
                        ConceptMastery.objects.create(user=user, concept=concept)
                        mastery_given = True
                        has_mastery = True

                return JsonResponse({
                    'success': True,
                    'new_score': session.total_score,
                    'score_gained': score_gained,
                    'mastery_given': mastery_given,
                    'has_mastery': has_mastery,
                    'resolved_count': resolved_count if 'resolved_count' in locals() else 0,
                    'concept': concept
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
