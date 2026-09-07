"""Revinteq v3 — Accounts Models"""
from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user               = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=200, blank=True, default='')
    phone_number = models.CharField(max_length=20, blank=True, default='')
    timezone           = models.CharField(max_length=50, default='Africa/Nairobi')
    onboarding_complete= models.BooleanField(default=False)
    created_at         = models.DateTimeField(auto_now_add=True)
    updated_at         = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profiles'

    def __str__(self):
        return f"Profile: {self.user.email}"
