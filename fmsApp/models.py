from turtle import title
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from cryptography.fernet import Fernet
from django.conf import settings
import base64, os
from django.dispatch import receiver

class TrainingRecord(models.Model):
    facility_assigned = models.CharField(max_length=100)
    section_assigned = models.CharField(max_length=100)
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='training_records',null=True)  # This is the logged-in staff user

    supervisor_name = models.CharField(max_length=100)
    supervisor_date = models.DateField()

    records_maintenance_personnel = models.CharField(max_length=100)
    records_maintenance_date = models.DateField()

    date_reviewed = models.DateField(auto_now_add=True)  # Auto-filled for staff
    printed_name = models.CharField(max_length=100)  # Entered by staff
    signature = models.CharField(max_length=10)       # Entered by staff

    qa_review_date = models.DateField(null=True, blank=True)
    qa_printed_name = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='qa_reviews')
    qa_signature = models.CharField(max_length=10, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.employee.username} - {self.date_reviewed}"
    
class Post(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Verified', 'Verified'),
        ('Invalid', 'Invalid'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=250)
    description = models.TextField(blank=True, null=True)
    file_path = models.FileField(upload_to='uploads/',blank=True, null=True)
    date_created = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_posts')
    
    def __str__(self):
        return self.user.username + '-' + self.title

    def get_share_url(self):
        fernet = Fernet(settings.ID_ENCRYPTION_KEY)
        value = fernet.encrypt(str(self.pk).encode())
        value = base64.urlsafe_b64encode(value).decode()
        return reverse("share-file-id", kwargs={"id": (value)})

@receiver(models.signals.post_delete, sender=Post)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.file_path:
        if os.path.isfile(instance.file_path.path):
            os.remove(instance.file_path.path)

@receiver(models.signals.pre_save, sender=Post)
def auto_delete_file_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return False

    try:
        old_file = sender.objects.get(pk=instance.pk).file_path
    except sender.DoesNotExist:
        return False

    new_file = instance.file_path
    if not old_file == new_file:
        if os.path.isfile(old_file.path):
            os.remove(old_file.path)
    