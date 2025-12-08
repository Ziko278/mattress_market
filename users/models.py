from django.db import models
from django.contrib.auth.models import User

from backend import settings
from django.utils.module_loading import import_string


def get_storage():
    return import_string(settings.STORAGE_BACKEND)()


class UserProfileModel(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, storage=get_storage())

    def __str__(self):
        return self.user.username