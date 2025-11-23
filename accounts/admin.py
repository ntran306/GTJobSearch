import csv
from django.http import HttpResponse
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from accounts.models import JobSeekerProfile, RecruiterProfile

admin.site.unregister(User)


def export_users_csv(modeladmin, request, queryset):
    """Export selected users to CSV with role-specific details"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Username', 'Email', 'Role', 'Is Staff', 'Is Active', 
        'Date Joined', 'Last Login',
        # Recruiter-specific fields
        'Company', 'Recruiter Name', 'Website', 'Description', 'Location',
        'Jobs Posted (Titles)', 'Jobs Posted (Count)',
        # Job Seeker-specific fields
        'Headline', 'Skills', 'Education', 'Work Experience', 
        'Links', 'Projects', 'Applications (Job Titles)', 
        'Applications (Status)', 'Applications (Count)'
    ])
    
    for user in queryset.select_related('jobseekerprofile', 'recruiterprofile').prefetch_related(
        'recruiterprofile__jobs', 'applications__job'
    ):
        # Determine role
        if user.is_superuser or user.is_staff:
            role = "Admin"
        elif hasattr(user, "recruiterprofile"):
            role = "Recruiter"
        elif hasattr(user, "jobseekerprofile"):
            role = "Job Seeker"
        else:
            role = "Unassigned"
        
        # Initialize all fields as empty
        company = recruiter_name = website = description = location = ''
        jobs_titles = jobs_count = ''
        headline = skills = education = work_exp = links = projects = ''
        app_titles = app_status = app_count = ''
        
        # Recruiter-specific data
        if hasattr(user, 'recruiterprofile'):
            recruiter = user.recruiterprofile
            company = recruiter.company or ''
            recruiter_name = recruiter.name or ''
            website = recruiter.website or ''
            description = recruiter.description or ''
            location = recruiter.location or ''
            
            # Get all jobs posted by this recruiter
            jobs = recruiter.jobs.all()
            jobs_count = jobs.count()
            jobs_titles = ' | '.join([job.title for job in jobs]) if jobs_count > 0 else ''
        
        # Job Seeker-specific data
        if hasattr(user, 'jobseekerprofile'):
            jobseeker = user.jobseekerprofile
            headline = jobseeker.headline or ''
            skills_list = jobseeker.skills.all()
            skills = ', '.join([skill.name for skill in skills_list])
            education = jobseeker.education or ''
            work_exp = jobseeker.work_experience or ''
            links = jobseeker.links or ''
            projects = jobseeker.projects or ''
            location = jobseeker.location or ''
            
            # Get all applications by this job seeker
            applications = user.applications.select_related('job').all()
            app_count = applications.count()
            if app_count > 0:
                app_titles = ' | '.join([app.job.title for app in applications])
                app_status = ' | '.join([f"{app.job.title}: {app.status}" for app in applications])
            else:
                app_titles = ''
                app_status = ''
        
        writer.writerow([
            user.username,
            user.email,
            role,
            user.is_staff,
            user.is_active,
            user.date_joined.strftime('%Y-%m-%d %H:%M:%S') if user.date_joined else '',
            user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else '',
            # Recruiter fields
            company,
            recruiter_name,
            website,
            description,
            location if role == "Recruiter" else '',
            jobs_titles,
            jobs_count,
            # Job Seeker fields
            headline,
            skills,
            education,
            work_exp,
            links,
            projects,
            app_titles,
            app_status,
            app_count,
        ])
    
    return response

export_users_csv.short_description = "Export selected users to CSV"


@admin.register(User)
class GroupedUserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "is_staff", "user_role")
    list_filter = ("is_staff", "is_superuser", "is_active")
    
    # Override the change list template to use our custom grouped version
    change_list_template = "admin/auth/user/change_list.html"
    
    # Enable actions and specify which ones to show
    actions = ['delete_selected', 'export_users_csv']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Optimize queries by selecting related profiles
        qs = qs.select_related("jobseekerprofile", "recruiterprofile")
        return qs

    def user_role(self, obj):
        """Display the user's role based on their profile"""
        if obj.is_superuser or obj.is_staff:
            return "Admin"
        elif hasattr(obj, "recruiterprofile"):
            return "Recruiter"
        elif hasattr(obj, "jobseekerprofile"):
            return "Job Seeker"
        else:
            return "Unassigned"
    
    user_role.short_description = "Role"
    user_role.admin_order_field = "is_staff"

    def get_role_group(self, obj):
        """Helper method to determine which group a user belongs to"""
        if obj.is_superuser or obj.is_staff:
            return ("Admins", 1)
        elif hasattr(obj, "recruiterprofile"):
            return ("Recruiters", 2)
        elif hasattr(obj, "jobseekerprofile"):
            return ("Job Seekers", 3)
        else:
            return ("Unassigned", 4)

    def changelist_view(self, request, extra_context=None):
        """Override changelist view to add grouped data"""
        response = super().changelist_view(request, extra_context)
        
        # Only modify if we're displaying the list (not exporting, etc.)
        if hasattr(response, 'context_data') and 'cl' in response.context_data:
            cl = response.context_data['cl']
            
            # Group users by role
            grouped_users = {}
            for user in cl.result_list:
                role_name, role_order = self.get_role_group(user)
                if role_name not in grouped_users:
                    grouped_users[role_name] = {
                        'name': role_name,
                        'order': role_order,
                        'users': []
                    }
                grouped_users[role_name]['users'].append(user)
            
            # Sort groups by order
            sorted_groups = sorted(grouped_users.values(), key=lambda x: x['order'])
            
            response.context_data['grouped_users'] = sorted_groups
            
            # Ensure action choices are available
            if 'action_form' in response.context_data:
                response.context_data['actions_on_top'] = True
                response.context_data['actions_on_bottom'] = True
        
        return response

    class Media:
        css = {
            "all": ("admin/css/admin_grouped_users.css",)
        }

    def delete_model(self, request, obj):
        """Custom delete to ensure complete cleanup."""
        username = obj.username
        super().delete_model(request, obj)
        self.message_user(request, f"User '{username}' and all related data have been deleted.")

    def delete_queryset(self, request, queryset):
        """Custom bulk delete to ensure complete cleanup."""
        count = queryset.count()
        super().delete_queryset(request, queryset)
        self.message_user(request, f"{count} user(s) and all their related data have been deleted.")
    
    def get_actions(self, request):
        """Override to show delete and export actions"""
        actions = super().get_actions(request)
        # Add our custom export action
        actions['export_users_csv'] = (export_users_csv, 'export_users_csv', export_users_csv.short_description)
        # Keep only the delete_selected and export actions
        if 'delete_selected' in actions:
            return {
                'delete_selected': actions['delete_selected'],
                'export_users_csv': actions['export_users_csv']
            }
        return {'export_users_csv': actions['export_users_csv']}