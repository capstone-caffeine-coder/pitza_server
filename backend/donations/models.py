from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.contrib.auth import get_user_model


User = get_user_model()

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
    
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='donation_requests')
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
    donator_registered_id = models.CharField(
        max_length=11,
        validators=[
            RegexValidator(
                regex=r'^\d{6}-\d{4}$',
                message='ID must be in the format XXXXXX-XXXX (6 digits, hyphen, 4 digits).',
                code='invalid_donator_id'
            )
        ],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    


class RejectedMatchRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rejected_matches')
    donation_request = models.ForeignKey(DonationRequest, on_delete=models.CASCADE, related_name='rejected_matches')
    
    class Meta:
        unique_together = ('user', 'donation_request')

class SelectedMatchRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='selected_matches')
    donation_request = models.ForeignKey(DonationRequest, on_delete=models.CASCADE, related_name='selected_matches')
    selected_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'donation_request')
        
