from django.conf import settings
from django.db import models
from django.db.models import Q, UniqueConstraint

class Connection(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"
        DECLINED = "DECLINED", "Declined"

    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="connections_out")
    addressee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="connections_in")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            # Prevent duplicate pairs in either direction
            UniqueConstraint(
                fields=["requester", "addressee"],
                name="uniq_connection_direct"
            )
        ]

    def is_between(self, u1_id, u2_id):
        return {self.requester_id, self.addressee_id} == {u1_id, u2_id}