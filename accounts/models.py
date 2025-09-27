from django.db import models
from django.contrib.auth.models import User

class JobSeekerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    headline = models.CharField(max_length=255, blank=True)
    skills = models.TextField(blank=True)
    education = models.TextField(blank=True)
    work_experience = models.TextField(blank=True)
    links = models.URLField(blank=True, null=True)  # <-- make optional

    def __str__(self):
        return f"{self.user.username}'s Profile"

class RecruiterProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} (Recruiter)"
