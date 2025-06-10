# login/serializers.py

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import User
from datetime import date

class UserProfileSerializer(serializers.ModelSerializer):
    birthdate = serializers.DateField(
        format='%m/%d/%Y',
        input_formats=['%m/%d/%Y', '%Y-%m-%d', None]
    )

    profile_picture = serializers.URLField(
        source='profile_picture_key',
        required=False,
        allow_blank=True,
        allow_null=True
    )

    class Meta:
        model = User
        fields = [
            'id', 'email', 'kakao_id', 'nickname', 'birthdate', 'sex',
            'blood_type', 'profile_picture', 'age',
            # --- FIX: REMOVE 'password' from fields entirely! ---
            # If you are never using passwords, it should not be in this serializer.
        ]
        read_only_fields = ['id', 'email', 'kakao_id', 'age']
        extra_kwargs = {
            # --- FIX: REMOVE extra_kwargs for 'password' ---
        }

    # --- FIX: Remove the custom update method ---
    # The default ModelSerializer.update() handles everything else automatically
    # and correctly when 'password' is not in 'fields'.
    # You only need a custom update() if you have non-standard logic for other fields.
    # For common profile updates, the default is best.
    # def update(self, instance, validated_data):
    #     # ... (code for password handling removed)
    #     # ... (rest of the update logic, which is now handled by default)
    #     return instance