from django.db import models
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import os

local_storage = FileSystemStorage(
    location=os.path.join('media', 'donation_images'),
    base_url='/media/donation_images/'
)

class DonationPost(models.Model):  # 기부하기 탭
    BLOOD_TYPES = [('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
                   ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-')]
    GENDER_CHOICES = [('M', '남성'), ('F', '여성')]

    donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    image = models.ImageField(upload_to='', storage=local_storage, blank=True, null=True)
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPES)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    region = models.CharField(max_length=100)
    introduction = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"[기부] {self.donor.email}"

class RequestPost(models.Model):  # 요청하기 탭
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='', storage=local_storage, blank=True, null=True)
    blood_type = models.CharField(max_length=3, choices=DonationPost.BLOOD_TYPES)
    region = models.CharField(max_length=100)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"[요청] {self.requester.username}"
