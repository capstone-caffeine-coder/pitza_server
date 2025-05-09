from rest_framework import serializers
from django.contrib.auth.models import User
from .models import DonationRequest, RejectedMatchRequest, SelectedMatchRequest

class DonationRequestSerializer(serializers.HyperlinkedModelSerializer):
    requester = serializers.HyperlinkedRelatedField(
        queryset=User.objects.all(),
        # TODO: Replace with the actual view name of the User model
        view_name='user-detail' 
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


class RejectedMatchRequestSerializer(serializers.HyperlinkedModelSerializer):
    user = serializers.HyperlinkedRelatedField(
        queryset=User.objects.all(),
        # TODO: Replace with the actual view name of the User model
        view_name='user-detail' 
    )
    donation_request = serializers.HyperlinkedRelatedField(
        queryset=DonationRequest.objects.all(),
        # TODO: Replace with the actual view name of the DonationRequest model
        view_name='donations-retrieve' 
    )
    class Meta:
        model = RejectedMatchRequest
        fields = ['id', 'user', 'donation_request']

class SelectedMatchRequestSerializer(serializers.HyperlinkedModelSerializer):
    user = serializers.HyperlinkedRelatedField(
        queryset=User.objects.all(),
        # TODO: Replace with the actual view name of the User model
        view_name='user-detail' 
    )
    donation_request = serializers.HyperlinkedRelatedField(
        queryset=DonationRequest.objects.all(),
        # TODO: Replace with the actual view name of the DonationRequest model
        view_name='donations-retrieve' 
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
    