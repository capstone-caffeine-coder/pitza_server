from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.conf import settings
from .models import DonationRequest, RejectedMatchRequest, SelectedMatchRequest


User = get_user_model()

class DonationRequestSerializer(serializers.ModelSerializer):
    requester = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
    ) 
    
    image = serializers.ImageField(use_url=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = DonationRequest
        fields = ['id', 'requester', 'name', 'age', 'sex', 'blood_type', 'content', 'image', 'image_url','location', 'donation_due_date', 'donator_registered_id', 'created_at']
        read_only_fields = ['image_url']
        
    def get_image_url(self, obj):
        if obj.image and obj.image.name: # Check if an image file exists and has a name
            
            return f"{settings.MINIO_PUBLIC_URL_BASE}/{settings.MINIO_STORAGE_MEDIA_BUCKET_NAME}/{obj.image.name}"
        return None

class CreateDonationRequestSerializer(serializers.Serializer):
    requester = serializers.IntegerField()
    name = serializers.CharField()
    age = serializers.IntegerField()
    sex = serializers.CharField()
    blood_type = serializers.CharField()
    content = serializers.CharField()
    location = serializers.CharField()
    donation_due_date = serializers.DateField()
    donator_registered_id = serializers.CharField()
    image = serializers.ImageField(required=True)


class RejectedMatchRequestSerializer(serializers.ModelSerializer):
    user =serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
    )
    donation_request =serializers.PrimaryKeyRelatedField(
        queryset=DonationRequest.objects.all(),
    )
    class Meta:
        model = RejectedMatchRequest
        fields = ['id', 'user', 'donation_request']

class SelectedMatchRequestSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
    )
    donation_request = serializers.PrimaryKeyRelatedField(
        queryset=DonationRequest.objects.all(),
    )
    class Meta:
        model = SelectedMatchRequest
        fields = ['id', 'user', 'donation_request']
        
class MessageSerializer(serializers.Serializer):
    message = serializers.CharField()
    
class DonationRequestIdSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    
class DonatorRegisteredIdSerializer(serializers.Serializer):
    donator_registered_id = serializers.CharField()

class MatchRequestSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
    )
    blood_type = serializers.CharField()
    age = serializers.IntegerField()
    sex = serializers.CharField()
    location = serializers.CharField()
    next_donation_date = serializers.DateField()

