from rest_framework import serializers
from .models import BloodCenter

class BloodCenterSerializer(serializers.ModelSerializer):
    distance = serializers.FloatField(required=False)  # distance 필드는 nearby에서만 사용

    class Meta:
        model = BloodCenter
        fields = [
            "id",
            "name",
            "address",
            "phone",
            "center_type",
            "blood_office",
            "latitude",
            "longitude",
            "distance",
        ]
