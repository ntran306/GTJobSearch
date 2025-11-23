import csv
from django.contrib import admin
from django.http import HttpResponse
from applications.models import Application


def export_applications_csv(modeladmin, request, queryset):
    """Export selected applications to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="applications_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'ID', 'User', 'Job Title', 'Company', 'Status', 'Applied At', 'Note'
    ])
    
    for app in queryset.select_related('user', 'job'):
        writer.writerow([
            app.id,
            app.user.username,
            app.job.title,
            app.job.company,
            app.status,
            app.applied_at.strftime('%Y-%m-%d %H:%M:%S'),
            app.note or '',
        ])
    
    return response

export_applications_csv.short_description = "Export selected applications to CSV"


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'job', 'status', 'applied_at')
    list_filter = ('status', 'applied_at')
    search_fields = ('user__username', 'job__title', 'job__company')
    actions = [export_applications_csv]  # Changed from string to function reference