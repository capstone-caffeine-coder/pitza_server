from rest_framework import serializers
from .models import DonationPost, RequestPost

class DonationPostSerializer(serializers.ModelSerializer):
    receiver_id = serializers.IntegerField(source='donor.id', read_only=True)
    donor_username = serializers.SerializerMethodField()
    donor_profile_image = serializers.SerializerMethodField()
    image = serializers.ImageField(required=False) 

    class Meta:
        model = DonationPost
        fields = [
            'id',
            'receiver_id',
            'donor_username',
            'donor_profile_image',
            'image',
            'blood_type',
            'age',
            'gender',
            'region',
            'introduction',
            'created_at'
        ]

    def get_donor_username(self, obj):
        if obj.donor:
            return obj.donor.nickname or obj.donor.email or f"Kakao:{obj.donor.kakao_id}"
        return None

    def get_donor_profile_image(self, obj):
        if obj.donor and obj.donor.profile_picture_key:
            request = self.context.get('request')
            image_url = obj.donor.profile_picture_key.url
            return request.build_absolute_uri(image_url) if request else image_url
        return None

class RequestPostSerializer(serializers.ModelSerializer):
    receiver_id = serializers.IntegerField(source='requester.id', read_only=True)
    requester_username = serializers.CharField(source='requester.nickname', read_only=True)
    requester_profile_image = serializers.SerializerMethodField()
    image = serializers.ImageField(required=False) 

    class Meta:
        model = RequestPost
        fields = [
            'id', 
            'receiver_id',
            'requester_username',
            'requester_profile_image',
            'image', 
            'blood_type',
            'region', 
            'reason', 
            'created_at']
        
        def get_requester_username(self, obj):
            if obj.requester:
                return obj.requester.nickname or obj.requester.email or f"Kakao:{obj.requester.kakao_id}"
            return None

        def get_requester_profile_image(self, obj):
            if obj.requester and obj.requester.profile_picture_key:
                request = self.context.get('request')
                image_url = obj.requester.profile_picture_key.url
                return request.build_absolute_uri(image_url) if request else image_url
            return None