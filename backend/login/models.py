from django.db import models

class User(models.Model):
    email = models.EmailField(unique=True, null=True, blank=True)
    kakao_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    nickname = models.CharField(max_length=100, blank=True)
    birthdate = models.DateField(null=True, blank=True)
    sex = models.CharField(max_length=10, blank=True)
    blood_type = models.CharField(max_length=3, blank=True)
    profile_picture = models.URLField(blank=True)

    def __str__(self):
        return self.email or f"Kakao:{self.kakao_id}"