# login/serializers.py

from rest_framework import serializers
from django.forms import ValidationError
from .models import User
import uuid
import requests
from io import BytesIO
from django.conf import settings

try:
    from .minio_utils import minio_client, MINIO_BUCKET_NAME
except ImportError:
    print("Warning: MinIO client not fully configured in serializers. Make sure you have 'minio_utils.py'.")
    minio_client = None
    MINIO_BUCKET_NAME = "default-profile-pictures"


class UserProfileSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()
    profile_picture_input = serializers.CharField(write_only=True, required=False, allow_blank=True)
    profile_picture_file = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'kakao_id', 'nickname', 'birthdate', 'sex',
            'blood_type', 'profile_picture', 'age', 'profile_picture_input',
            'profile_picture_file', 'password'
        ]
        read_only_fields = ['id', 'email', 'kakao_id', 'age']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False, 'allow_blank': True},
        }

    def get_profile_picture(self, obj):
        return obj.get_profile_picture_url()

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)

        profile_picture_input = validated_data.pop('profile_picture_input', None)
        profile_picture_file = validated_data.pop('profile_picture_file', None)

        new_profile_picture_key = instance.profile_picture_key

        if profile_picture_file:
            new_profile_picture_key = self._upload_file_to_minio(instance, profile_picture_file)
        elif profile_picture_input is not None:
            if profile_picture_input.strip() == '':
                new_profile_picture_key = None
            elif profile_picture_input.startswith(('http://', 'https://')):
                new_profile_picture_key = self._download_and_upload_url_to_minio(instance, profile_picture_input)
            else:
                raise serializers.ValidationError({'profile_picture_input': 'Invalid input: must be a valid URL or empty to clear.'})

        instance.profile_picture_key = new_profile_picture_key

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()

        return instance

    def _upload_file_to_minio(self, instance, uploaded_file):
        if minio_client is None:
            raise serializers.ValidationError("MinIO client not initialized. Check server configuration.")

        filename = f"profile_pictures/{instance.id}/{uuid.uuid4()}_{uploaded_file.name}"
        try:
            minio_client.put_object(
                MINIO_BUCKET_NAME,
                filename,
                uploaded_file.file,
                uploaded_file.size,
                content_type=uploaded_file.content_type
            )
            return filename
        except Exception as e:
            raise serializers.ValidationError({'profile_picture_file': f"Failed to upload profile picture file to storage: {e}"})

    def _download_and_upload_url_to_minio(self, instance, image_url):
        if minio_client is None:
            raise serializers.ValidationError("MinIO client not initialized. Check server configuration.")

        try:
            response = requests.get(image_url, stream=True, timeout=10)
            response.raise_for_status()

            content_type = response.headers.get('Content-Type', 'application/octet-stream')
            original_filename = image_url.split('/')[-1]
            if '.' not in original_filename:
                if 'image/jpeg' in content_type: original_filename += '.jpg'
                elif 'image/png' in content_type: original_filename += '.png'
                elif 'image/gif' in content_type: original_filename += '.gif'
                else: original_filename += '.bin'

            filename = f"profile_pictures/{instance.id}/{uuid.uuid4()}_{original_filename}"

            file_content = BytesIO(response.content)
            file_size = len(response.content)

            minio_client.put_object(
                MINIO_BUCKET_NAME,
                filename,
                file_content,
                file_size,
                content_type=content_type
            )
            return filename
        except requests.exceptions.RequestException as e:
            raise serializers.ValidationError({'profile_picture_input': f"Failed to download image from URL: {e}"})
        except Exception as e:
            raise serializers.ValidationError({'profile_picture_input': f"Failed to process image from URL: {e}"})