"""Models for the drf-firebase-token-auth application"""

from django.db import models
from django.contrib.auth import get_user_model


class FirebaseUser(models.Model):
    """Firebase user model

    This model connects a local user model to a Firebase user id.
    """
    uid = models.CharField(max_length=128, primary_key=True)
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.user.username

