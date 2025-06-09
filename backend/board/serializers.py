from rest_framework import serializers
from .models import DonationPost, RequestPost

class DonationPostSerializer(serializers.ModelSerializer):
    donor_username = serializers.SerializerMethodField()

    class Meta:
        model = DonationPost
        fields = ['id', 'donor_username', 'image', 'blood_type', 'age', 'gender', 'region', 'introduction', 'created_at']

    def get_donor_username(self, obj):
        if obj.donor:
            return obj.donor.username
        return None

class RequestPostSerializer(serializers.ModelSerializer):
    requester_username = serializers.CharField(source='requester.username', read_only=True)

    class Meta:
        model = RequestPost
        fields = ['id', 'requester_username', 'blood_type', 'region', 'reason', 'created_at']
