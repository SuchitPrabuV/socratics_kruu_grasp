from django.db import models
from django.utils import timezone

class Problem(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    starter_code = models.TextField()

    def __str__(self):
        return self.title

class StudentSession(models.Model):
    """Tracks student progress and score across their learning session"""
    session_id = models.CharField(max_length=100, unique=True)
    total_score = models.IntegerField(default=0)
    problems_solved = models.IntegerField(default=0)
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Session {self.session_id} - Score: {self.total_score}"

class Interaction(models.Model):
    user_code = models.TextField()
    error_log = models.TextField(blank=True, null=True)
    ai_hint = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # New fields for score tracking
    session_id = models.CharField(max_length=100, blank=True, null=True)
    was_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Interaction at {self.timestamp}"

