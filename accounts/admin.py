from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

admin.site.unregister(User)


@admin.register(User)
class GroupedUserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "user_role")
    list_filter = ("is_staff", "is_superuser", "is_active")
    
    # Override the change list template to use our custom grouped version
    change_list_template = "admin/auth/user/change_list.html"
    
    # Enable actions and specify which ones to show
    actions = ['delete_selected']

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
    user_role.admin_order_field = "is_staff"  # Allow sorting by role

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
        """
        Custom delete to ensure complete cleanup.
        Django's CASCADE should handle most relations, but this ensures logging.
        """
        username = obj.username
        super().delete_model(request, obj)
        self.message_user(request, f"User '{username}' and all related data have been deleted.")

    def delete_queryset(self, request, queryset):
        """
        Custom bulk delete to ensure complete cleanup.
        """
        count = queryset.count()
        super().delete_queryset(request, queryset)
        self.message_user(request, f"{count} user(s) and all their related data have been deleted.")
    
    def get_actions(self, request):
        """
        Override to only show delete action
        """
        actions = super().get_actions(request)
        # Keep only the delete_selected action
        if 'delete_selected' in actions:
            return {'delete_selected': actions['delete_selected']}
        return {}