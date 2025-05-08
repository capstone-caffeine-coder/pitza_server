from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from unittest.mock import MagicMock, patch
from datetime import timedelta
import json

from .models import DonationRequest

class MatchTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        self.donation_data = {
            'id': 1,
            'requester_id': 2,
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
        
        self.match_input = {
            'user_id': 3,
            'blood_type': 'A-',
            'age': 10,
            'sex': 'female',
            'location': 'Incheon',
            'next_donation_date': '2025-04-29' 
        }
        
    def test_match_donation_request_when_match_is_selected(self):
        url = reverse('donations:match')
        
        # Create donation request
        url_create = reverse('donations:create')
        self.client.post(
            url_create,
            data={'request_data': json.dumps(self.donation_data)},
        )
        
        # Send match reqeust
        request_data = json.dumps(self.match_input)
        response = self.client.post(
            url,
            data={'request_data': request_data},
        )
        
        # Check response status code
        self.assertEqual(response.status_code, 200)
        
        # Check response data
        response_data = json.loads(response)
        
        self.assertEqual(response_data['id'], self.donation_data['id'])
        
        # Send select match
        url_select_match = reverse('donations:select_match')
        response = self.client.post(
            url_select_match,
            data={'request_id': self.donation_data['id'], 'user_id': self.match_input['user_id']},
        )
        
        # Check response status code
        self.assertEqual(response.status_code, 200)

        # Check response data contains donator_registered_id
        response_data = json.loads(response)
        self.assertEqual(response_data['donator_registered_id'], self.donation_data['donator_registered_id'])

    def test_match_donation_request_when_match_is_rejected(self):
        url = reverse('donations:match')
        
        # Create donation request
        url_create = reverse('donations:create')
        self.client.post(
            url_create,
            data={'request_data': json.dumps(self.donation_data)},
        )
        
        # Send match reqeust
        request_data = json.dumps(self.match_input)
        response = self.client.post(
            url,
            data={'request_data': request_data},
        )
        
        # Check response status code
        self.assertEqual(response.status_code, 201)
      
        
        # Send reject match
        url_reject_match = reverse('donations:reject_match')
        response = self.client.post(
            url_reject_match,
            data={'request_id': self.donation_data['id'], 'id': self.match_input['user_id']},
        )
        
        # Check response status code
        self.assertEqual(response.status_code, 200)

        # Check response data contains donator_registered_id
        response_data = json.loads(response)
        self.assertEqual(response_data['donator_registered_id'], self.donation_data['donator_registered_id'])



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
        # user authentication
        
        self.donation_request_data = {
            'requester_id': 2,
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
        
        self.get_donation_request_data_by_id = {
            'id': 2
        }

    def test_create_donation_request_success(self):
        
        url = reverse('donations:create')
       
        request_data = self.donation_request_data
        
        post_data = json.dumps({
            'request_data':  {
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
        })

        response = self.client.post(
            url,
            json.loads(post_data),
        )

        self.assertEqual(response.status_code, 201)

        response_data = response.json()
        self.assertEqual(response_data, {'id': 123})
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
        )
        
        # Check response status code indicates error
        self.assertEqual(response.status_code, 400)
        
        # Verify no donation request was created
        self.assertEqual(DonationRequest.objects.count(), 0)

    def test_get_donation_request_by_id(self):
        """Test getting a donation request by its ID"""
        # First create a donation request
        url_create = reverse('donations:create')
        self.client.post(
            url_create,
            data={'request_data': json.dumps()},
        )
        
        # Get the created donation request's ID
        donation = DonationRequest.objects.first()
        request_id = donation.id
        
        # Test retrieving the donation request by ID
        url_detail = reverse('donations:detail', args=[request_id])
        response = self.client.get(url_detail)
        
        # Check response status code
        self.assertEqual(response.status_code, 200)
        
        # Parse response data
        response_data = json.loads(response.content)
        
        # Verify returned data matches the created donation request
        self.assertEqual(response_data['id'], request_id)
        self.assertEqual(response_data['name'], self.donation_request_data['name'])
        self.assertEqual(response_data['age'], self.donation_request_data['age'])
        self.assertEqual(response_data['sex'], self.donation_request_data['sex'])
        self.assertEqual(response_data['blood_type'], self.donation_request_data['blood_type'])
        self.assertEqual(response_data['location'], self.donation_request_data['location'])
        self.assertEqual(response_data['content'], self.donation_request_data['content'])

    