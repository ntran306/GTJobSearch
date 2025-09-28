from django.core.management.base import BaseCommand
from jobs.models import Skill, PREDEFINED_SKILLS

class Command(BaseCommand):
    help = 'Populate the database with predefined skills'

    def handle(self, *args, **options):
        created_count = 0
        
        for skill_name in PREDEFINED_SKILLS:
            skill, created = Skill.objects.get_or_create(name=skill_name)
            if created:
                created_count += 1
                self.stdout.write(f"Created skill: {skill_name}")
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} new skills. '
                f'Total skills in database: {Skill.objects.count()}'
            )
        )