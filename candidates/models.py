from django.db import models
from django.contrib.auth.models import User

#class Skill(models.Model):
#    name = models.CharField(max_length=100)
#
#    def __str__(self):
#        return self.name

#class Project(models.Model):
#    title = models.CharField(max_length=100)
#    description = models.TextField(blank=True)
#
#    def __str__(self):
#        return self.title

#class Candidate(models.Model):
#    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='candidate_profile')
#    location = models.CharField(max_length=100, blank=True)
#    bio = models.TextField(blank=True)
#    skills = models.ManyToManyField(Skill, blank=True)
#    projects = models.ManyToManyField(Project, blank=True)

#    def __str__(self):
#        return self.user.username


class SavedFilter(models.Model):
    recruiter = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="saved_candidate_filters"
    )
    skill = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    radius = models.IntegerField(null=True, blank=True)
    project = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # NEW: Enable notifications for this filter
    notify_on_match = models.BooleanField(default=True)
    
    def is_empty(self):
        return not (self.skill or self.location or self.project or self.radius)
    
    def matches_profile(self, profile):
        """Check if a candidate profile matches this filter"""
        # Skip recruiter profiles
        if profile.is_recruiter:
            return False
    
        # Check skill match (skills is a CharField in your model)
        if self.skill:
            profile_skills = profile.skills.lower() if profile.skills else ""
            if self.skill.lower() not in profile_skills:
                return False
    
        # Check location match
        if self.location and profile.location:
            if self.location.lower() not in profile.location.lower():
                return False
    
        # Check project match
        if self.project and profile.projects:
            if self.project.lower() not in profile.projects.lower():
                return False
    
        return True
    
    def __str__(self):
        return f"SavedFilter #{self.id} for {self.recruiter.username}"


class FilterNotification(models.Model):
    """Notifications for new candidate matches"""
    NOTIFICATION_TYPES = [
        ('new_match', 'New Candidate Match'),
    ]
    
    recruiter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='filter_notifications')
    saved_filter = models.ForeignKey(SavedFilter, on_delete=models.CASCADE, related_name='notifications')
    candidate = models.ForeignKey(User, on_delete=models.CASCADE, related_name='match_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='new_match')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for {self.recruiter.username} - {self.candidate.username}"

