# your_project/login/serializers.py

from rest_framework import serializers
from .models import User # Import your custom User model

class UserProfileSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'kakao_id', 'nickname', 'birthdate', 'sex',
            'blood_type', 'profile_picture', 'age', 'password',
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)


        instance = super().update(instance, validated_data)


        if password:
            instance.set_password(password)
            instance.save(update_fields=['password'])

        instance.save()
        return instance
