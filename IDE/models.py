from django.db import models

class Problem(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    starter_code = models.TextField()

    def __str__(self):
        return self.title

class Interaction(models.Model):
    user_code = models.TextField()
    error_log = models.TextField(blank=True, null=True)
    ai_hint = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Interaction at {self.timestamp}"

class ConceptMastery(models.Model):
    concept = models.CharField(max_length=100)
    score = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.concept}: {self.score}"
