from django.db import models
from datetime import date

class User(models.Model):
    email = models.EmailField(unique=True, null=True, blank=True)
    kakao_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    nickname = models.CharField(max_length=100, blank=True)
    birthdate = models.DateField(null=True, blank=True)
    sex = models.CharField(max_length=10, blank=True)
    blood_type = models.CharField(max_length=3, blank=True)
    profile_picture = models.URLField(blank=True)

    @property
    def age(self):
        # Returns None if birthdate is not set.
        if self.birthdate:
            today = date.today()
            # Calculate initial age difference in years
            age = today.year - self.birthdate.year
            # Adjust age if the current date is before the birth month/day
            if today.month < self.birthdate.month or (today.month == self.birthdate.month and today.day < self.birthdate.day):
                age -= 1
            return age
        return None # Return None or 0 if birthdate is not set

    def __str__(self):
        return self.nickname or self.email or f"Kakao:{self.kakao_id}"