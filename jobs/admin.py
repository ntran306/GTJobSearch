import csv
from django.contrib import admin
from django.http import HttpResponse
from .models import Job, Skill


def export_jobs_csv(modeladmin, request, queryset):
    """Export selected jobs to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="jobs_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Title', 'Company', 'Location', 'Recruiter', 
        'Pay Min', 'Pay Max', 'Pay Type', 'Visa Sponsorship',
        'Is Approved', 'Is Flagged', 'Is Archived', 'Created At',
        'Description', 'Required Skills', 'Preferred Skills'
    ])
    
    for job in queryset.select_related('recruiter'):
        required_skills = ', '.join([skill.name for skill in job.required_skills.all()])
        preferred_skills = ', '.join([skill.name for skill in job.preferred_skills.all()])
        recruiter_name = job.recruiter.name if job.recruiter else 'N/A'
        
        writer.writerow([
            job.id,
            job.title,
            job.company,
            job.location,
            recruiter_name,
            job.pay_min,
            job.pay_max,
            job.pay_type,
            job.visa_sponsorship,
            job.is_approved,
            job.is_flagged,
            job.is_archived,
            job.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            job.description,  # Added description
            required_skills,
            preferred_skills,
        ])
    
    return response

export_jobs_csv.short_description = "Export selected jobs to CSV"


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "recruiter", "is_approved", "is_flagged", "created_at")
    list_filter = ("is_approved", "is_flagged", "created_at", "company")
    search_fields = ("title", "company", "description")

    # Add export action to your existing actions
    actions = ["approve_jobs", "flag_jobs", "archive_jobs", export_jobs_csv]

    @admin.action(description="Approve selected jobs")
    def approve_jobs(self, request, queryset):
        queryset.update(is_approved=True)

    @admin.action(description="Flag selected jobs (possible spam)")
    def flag_jobs(self, request, queryset):
        queryset.update(is_flagged=True)

    @admin.action(description="Archive selected jobs")
    def archive_jobs(self, request, queryset):
        queryset.update(is_archived=True)


# Register Skill model for easy management
@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)