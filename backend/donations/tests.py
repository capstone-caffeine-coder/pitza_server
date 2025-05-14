import uuid
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from user.models import User
from app.models import MyModel
from rest_framework.test import APIRequestFactory
from .models import DonationRequest

# Using the standard RequestFactory API to create a form POST request
factory = APIRequestFactory()
request = factory.get('/donations/', {'id': 1})
