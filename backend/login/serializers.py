# login/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError # Import for potential custom validation
from datetime import date # Needed if doing custom date validation

User = get_user_model()

# Serializer for the incoming POST request data (Deserialization & Validation)
class ProfileSetupRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for handling incoming profile setup data.
    Uses ModelSerializer to automatically map to User model fields
    and leverage model field validations.
    """
    # birthdate is automatically handled by DateField in ModelSerializer based on model
    # sex and blood_type validation against choices (if defined on model) is automatic
    # nickname max_length validation is automatic

    class Meta:
        model = User
        fields = [
            'nickname',
            'birthdate',
            'sex',
            'blood_type',
            'profile_picture',
        ]
        # If birthdate, sex, blood_type are *not* required on the model,
        # but you want them required in the API request, you can add:
        # extra_kwargs = {
        #     'birthdate': {'required': True},
        #     'sex': {'required': True},
        #     'blood_type': {'required': True},
        # }

    # Optional: Add custom validation for specific fields if needed
    # def validate_birthdate(self, value):
    #     """
    #     Example of custom validation for birthdate (e.g., must be in the past).
    #     """
    #     if value and value > date.today():
    #         raise serializers.ValidationError("Birthdate cannot be in the future.")
    #     return value

    # Note: ModelSerializer handles most basic validation (required, max_length, choices, field types)
    # Custom validation methods like validate_<field_name> are for more complex rules.


# Serializer for the outgoing 200 OK Response data (Serialization)
class ProfileSetupResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for structuring the successful profile setup response.
    """
    # Include fields you want to return to the client after successful update
    message = serializers.CharField(read_only=True, help_text="Success message") # Add a custom message field

    class Meta:
        model = User
        fields = [
            'id',
            'email', # Include if you want to return email
            'kakao_id', # Include if you want to return kakao_id
            'nickname',
            'profile_picture',
            # Add other fields from the User model you want in the response
            'message', # Include the custom message field
        ]
        # Make fields read-only if they should not be settable via this serializer
        # (ModelSerializer fields are read/write by default unless specified)
        # read_only_fields = ['id', 'email', 'kakao_id'] # Example

        # Serializer for the incoming POST request body for get_user_by_session_api
class GetUserBySessionRequestSerializer(serializers.Serializer):
    """
    Serializer for validating the session_key in the request body.
    """
    # Use CharField with validation constraints if needed (e.g., max_length=32)
    session_key = serializers.CharField(max_length=200, required=True) # Adjust max_length as needed


# Serializer for the outgoing 200 OK Response data for get_user_by_session_api
class UserInfoResponseSerializer(serializers.Serializer):
    """
    Serializer for structuring the user information response, including profile completeness.
    """
    id = serializers.IntegerField()
    email = serializers.EmailField(allow_null=True, required=False) # Use EmailField for format validation
    kakao_id = serializers.CharField(allow_null=True, required=False)
    nickname = serializers.CharField(allow_null=True, required=False)
    is_profile_complete = serializers.BooleanField()

    # You can add a method to get the user instance if needed elsewhere,
    # but for serialization only, the above fields are sufficient.
    # def update(self, instance, validated_data):
    #     pass # This is a read-only serializer for response, update/create not needed

    # def create(self, validated_data):
    #     pass # This is a read-only serializer for response, update/create not needed
