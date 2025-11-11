from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from cryptography.fernet import Fernet
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save
import base64, os


########## USER PROFILE MODEL ##########
def user_profile_path(instance, filename):
    # Upload images to MEDIA_ROOT/profile_pics/user_<id>/<filename>
    return f'profile_pics/user_{instance.user.id}/{filename}'


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_image = models.ImageField(upload_to=user_profile_path, default='profile_pics/useravatar.jpg', blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


# Automatically create or update the user profile whenever a user is created or saved
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
    else:
        instance.profile.save()



########## DOCUMENT MODEL ##########
class Document(models.Model):
    SECTION_CHOICES = [
        ("section1", "Section 1: Verification of Job Qualifications"),
        ("section2", "Section 2: Department Orientation Records"),
        ("section3", "Section 3: Education, Training, Competency"),
    ]

    section = models.CharField(max_length=20, choices=SECTION_CHOICES)
    doc_type = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="documents/")
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("expired", "Expired"),
        ("invalid", "Invalid"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    reviewer_feedback = models.TextField(blank=True)

    def __str__(self):
        return f"{self.doc_type} - {self.uploaded_by.username}"


    