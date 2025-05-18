from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from minio_storage.storage import MinioStorage
from minio import Minio

import os
from django.conf import settings

minio_client = Minio(
    "minio:9000",
    access_key=os.getenv("MINIO_ACCESS_KEY"),
    secret_key=os.getenv("MINIO_SECRET_KEY"),
    secure=os.getenv("MINIO_USE_HTTPS") # Use secure=True for HTTPS
)


class DonationRequest(models.Model):
    SEX_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    
    BLOOD_TYPE_CHOICES = [
        ('A+', 'A Positive'),
        ('A-', 'A Negative'),
        ('B+', 'B Positive'),
        ('B-', 'B Negative'),
        ('AB+', 'AB Positive'),
        ('AB-', 'AB Negative'),
        ('O+', 'O Positive'),
        ('O-', 'O Negative'),
    ]
    
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='donation_requests')
    name = models.CharField(max_length=255)
    age = models.IntegerField(validators=[MinValueValidator(16), MaxValueValidator(70)])
    sex = models.CharField(max_length=1, choices=SEX_CHOICES)
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPE_CHOICES)
    content = models.TextField()
    #image = models.ImageField(upload_to='donation_requests/', null=True, blank=True)
    image = models.ImageField(
        upload_to='donation_images/', 
        blank=True,
        null=False
        )
    location = models.CharField(max_length=255)
    donation_due_date = models.DateField()
    donator_registered_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    


class RejectedMatchRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='rejected_matches')
    donation_request = models.ForeignKey(DonationRequest, on_delete=models.CASCADE, related_name='rejected_matches')
    
    class Meta:
        unique_together = ('user', 'donation_request')

class SelectedMatchRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='selected_matches')
    donation_request = models.ForeignKey(DonationRequest, on_delete=models.CASCADE, related_name='selected_matches')
    selected_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'donation_request')
        
