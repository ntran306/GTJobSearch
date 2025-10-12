from django.contrib import admin
from .models import Candidate, Skill, Project

admin.site.register(Candidate)
admin.site.register(Skill)
admin.site.register(Project)
