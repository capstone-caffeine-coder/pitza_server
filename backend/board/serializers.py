from rest_framework import serializers
from .models import DonationPost, RequestPost

class DonationPostSerializer(serializers.ModelSerializer):
    donor_username = serializers.SerializerMethodField()
    donor_profile_image = serializers.SerializerMethodField()

    class Meta:
        model = DonationPost
        fields = [
            'id',
            'donor_username',
            'donor_profile_image',  # 추가
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
        if obj.donor and obj.donor.profile_picture:
            request = self.context.get('request')
            image_url = obj.donor.profile_picture.url
            # 절대 URL로 변환
            return request.build_absolute_uri(image_url) if request else image_url
        return None

class RequestPostSerializer(serializers.ModelSerializer):
    requester_username = serializers.CharField(source='requester.nickname', read_only=True)

    class Meta:
        model = RequestPost
        fields = ['id', 'requester_username', 'blood_type', 'region', 'reason', 'created_at']
