from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError

class JobsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jobs'

    def ready(self):
        from .models import Skill
        try:
            for s in ["Python", "C++", "React", "SQL"]:
                Skill.objects.get_or_create(name=s)
        except (OperationalError, ProgrammingError):
            pass
