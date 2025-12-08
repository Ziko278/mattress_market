from django.db import models
from django.contrib.auth.models import User

from backend import settings


class UserProfileModel(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, storage=settings.STORAGE_BACKEND)

    def __str__(self):
        return self.user.username