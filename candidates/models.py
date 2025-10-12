from django.db import models
from django.contrib.auth.models import User

class Skill(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Project(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title

class Candidate(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='candidate_profile')
    location = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    skills = models.ManyToManyField(Skill, blank=True)
    projects = models.ManyToManyField(Project, blank=True)

    def __str__(self):
        return self.user.username
