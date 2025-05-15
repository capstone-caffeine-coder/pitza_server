from rest_framework import serializers
from django.contrib.auth.models import User
from .models import DonationRequest, RejectedMatchRequest, SelectedMatchRequest

class DonationRequestSerializer(serializers.ModelSerializer):
    requester = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
    ) 

    class Meta:
        model = DonationRequest
        fields = ['id', 'requester', 'name', 'age', 'sex', 'blood_type', 'content', 'image', 'location', 'donation_due_date', 'donator_registered_id', 'created_at']

class CreateDonationRequestSerializer(serializers.Serializer):
    requester = serializers.IntegerField()
    name = serializers.CharField()
    age = serializers.IntegerField()
    sex = serializers.CharField()
    blood_type = serializers.CharField()
    content = serializers.CharField()
    location = serializers.CharField()
    donation_due_date = serializers.DateField()
    donator_registered_id = serializers.IntegerField()
    image = serializers.ImageField()


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
    donator_registered_id = serializers.IntegerField()

class MatchRequestSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    blood_type = serializers.CharField()
    name = serializers.CharField()
    age = serializers.IntegerField()
    sex = serializers.CharField()
    location = serializers.CharField()
    next_donation_date = serializers.DateField()

