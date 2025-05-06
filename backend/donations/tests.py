from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import json

from .models import DonationRequest


class DonationRequestTests(TestCase):
    def setUp(self):
       
        self.user = {
            "id": 1,
            "name": "testuser",
            "age": "24",
            "sex": "F",
            "blood_type": "A-",
            "next_donation_date": "2025-05-06",
        }
      
        self.client = Client()
        
        # Skip user authentication
        
        self.donation_request_data = {
            'name': 'John Doe',
            'age': 35,
            'sex': 'M',
            'blood_type': 'A-',
            'content': 'Emergency blood donation needed',
            'image': 'test.jpg',
            'location': 'Seoul',
            'donation_due_date': (timezone.now().date() + timedelta(days=7)).isoformat(),
            'donator_registered_id': "12345678"
        }
    
    def test_create_donation_request_valid(self):
        """Test creating a donation request with valid data"""
        url = reverse('donations:create')
        
        # Send POST request with valid data
        response = self.client.post(
            url, 
            data={'request_data': json.dumps(self.donation_request_data)},
            content_type='application/json'
        )
        
        # Check response status code
        self.assertEqual(response.status_code, 201)
        
        # Verify donation request was created in the database
        self.assertEqual(DonationRequest.objects.count(), 1)
        
        # Verify donation request data was saved correctly
        donation = DonationRequest.objects.first()
        self.assertEqual(donation.name, self.donation_request_data['name'])
        self.assertEqual(donation.age, self.donation_request_data['age'])
        self.assertEqual(donation.sex, self.donation_request_data['sex'])
        self.assertEqual(donation.blood_type, self.donation_request_data['blood_type'])
        self.assertEqual(donation.location, self.donation_request_data['location'])
        self.assertEqual(donation.requester, self.user)
    
    def test_create_donation_request_invalid_blood_type(self):
        """Test creating a donation request with invalid blood type"""
        url = reverse('donations:create')
        
        # Create data with invalid blood type
        invalid_data = self.donation_request_data.copy()
        invalid_data['blood_type'] = 'X+'  # Invalid blood type
        
        # Send POST request with invalid data
        response = self.client.post(
            url, 
            data={'request_data': json.dumps(invalid_data)},
            content_type='application/json'
        )
        
        # Check response status code indicates error
        self.assertEqual(response.status_code, 400)
        
        # Verify no donation request was created
        self.assertEqual(DonationRequest.objects.count(), 0)
    
    def test_create_donation_request_missing_fields(self):
        """Test creating a donation request with missing required fields"""
        url = reverse('donations:create')
        
        # Create data with missing fields
        invalid_data = {
            'name': 'John Doe',
            # Missing other required fields
        }
        
        # Send POST request with invalid data
        response = self.client.post(
            url, 
            data={'request_data': json.dumps(invalid_data)},
            content_type='application/json'
        )
        
        # Check response status code indicates error
        self.assertEqual(response.status_code, 400)
        
        # Verify no donation request was created
        self.assertEqual(DonationRequest.objects.count(), 0)


