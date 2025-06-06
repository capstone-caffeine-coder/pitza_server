from rest_framework import serializers
from .models import DonationPost, RequestPost

class DonationPostSerializer(serializers.ModelSerializer):
    donor_username = serializers.CharField(source='donor.username', read_only=True)

    class Meta:
        model = DonationPost
        fields = ['id', 'donor_username', 'image', 'blood_type', 'age', 'gender', 'region', 'introduction', 'created_at']

class RequestPostSerializer(serializers.ModelSerializer):
    requester_username = serializers.CharField(source='requester.username', read_only=True)

    class Meta:
        model = RequestPost
        fields = ['id', 'requester_username', 'blood_type', 'region', 'reason', 'created_at']
