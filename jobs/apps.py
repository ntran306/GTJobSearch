from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError

class JobsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jobs'

    # Commented out ready due to a bunch of issues
#    def ready(self):
#        from .models import Skill
#        default_skills = [
#            "Python", "JavaScript", "C#", "React", "Django", "SQL", "HTML", "CSS"
#        ]
#        for skill_name in default_skills:
#            Skill.objects.get_or_create(name=skill_name)
