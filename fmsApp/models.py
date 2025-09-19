from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from cryptography.fernet import Fernet
from django.conf import settings
import base64, os
from django.dispatch import receiver

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
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    reviewer_feedback = models.TextField(blank=True)

    def __str__(self):
        return f"{self.doc_type} - {self.uploaded_by.username}"



    