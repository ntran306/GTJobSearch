from django.contrib import admin
from .models import Job

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "company", "recruiter", "is_approved", "is_flagged", "created_at")
    list_filter = ("is_approved", "is_flagged", "created_at", "company")
    search_fields = ("title", "company", "description")

    actions = ["approve_jobs", "flag_jobs", "archive_jobs"]

    @admin.action(description="Approve selected jobs")
    def approve_jobs(self, request, queryset):
        queryset.update(is_approved=True)

    @admin.action(description="Flag selected jobs (possible spam)")
    def flag_jobs(self, request, queryset):
        queryset.update(is_flagged=True)

    @admin.action(description="Archive selected jobs")
    def archive_jobs(self, request, queryset):
        queryset.update(is_archived=True)
