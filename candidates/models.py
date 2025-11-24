# candidates/models.py
from django.db import models
from django.contrib.auth.models import User


class SavedFilter(models.Model):
    recruiter = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="saved_candidate_filters"
    )

    skill = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    radius = models.IntegerField(null=True, blank=True)
    project = models.CharField(max_length=255, blank=True)
    notify_on_match = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def is_empty(self):
        return not (self.skill or self.location or self.project or self.radius)

    def matches_profile(self, profile):
        """Return True if JobSeekerProfile matches this filter."""
        print(f"\n--- Checking filter {self.id} for recruiter {self.recruiter.username} ---")
        print("Filter values:", {
            "skill": self.skill,
            "location": self.location,
            "project": self.project
        })
        print("Candidate values:", {
            "username": profile.user.username,
            "skills": [s.name for s in profile.skills.all()],
            "location": profile.location,
            "projects": profile.projects
        })

        # ---------------------------
        # SKILLS
        # ---------------------------
        if self.skill:
            candidate_skill_names = [s.name.lower() for s in profile.skills.all()]
            print("Skill check →", self.skill.lower(), "IN", candidate_skill_names)

            if self.skill.lower() not in candidate_skill_names:
                print("SKILL does not match")
                return False
            print("SKILL matches")

        # ---------------------------
        # LOCATION
        # ---------------------------
        if self.location:
            cand_loc = " ".join(filter(None, [
                profile.city.lower() if profile.city else "",
                profile.state_region.lower() if profile.state_region else "",
                profile.country.lower() if profile.country else "",
                (profile.location.lower() if profile.location else ""),
            ]))

            print("Location check → looking for:", self.location.lower(), "in", cand_loc)

            if self.location.lower() not in cand_loc:
                print("LOCATION does not match")
                return False

            print("LOCATION matches")

        # ---------------------------
        # PROJECTS
        # ---------------------------
        if self.project:
            cand_proj = profile.projects.lower() if profile.projects else ""
            print("Project check →", self.project.lower(), "IN", cand_proj)

            if self.project.lower() not in cand_proj:
                print("PROJECT does not match")
                return False

            print("PROJECT matches")

        print("FILTER MATCHES PROFILE!")
        return True

    def __str__(self):
        return f"SavedFilter #{self.id} for {self.recruiter.username}"


class FilterNotification(models.Model):
    recruiter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='filter_notifications')
    saved_filter = models.ForeignKey(SavedFilter, on_delete=models.CASCADE, related_name='notifications')
    candidate = models.ForeignKey(User, on_delete=models.CASCADE, related_name='match_notifications')

    notification_type = models.CharField(max_length=20, default='new_match')
    message = models.TextField()

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.recruiter.username} - {self.candidate.username}"
