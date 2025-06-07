# login/views/user_views.py

from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'kakao_id', 'nickname', 'birthdate', 'sex', 'blood_type', 'profile_picture', 'age']
        
    def get_profile_picture(self, obj):
        return obj.get_profile_picture_url()

@api_view(['GET'])
@swagger_auto_schema(responses={200: 'User details retrieved successfully'})
def user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    serializer = UserSerializer(user)

    return Response(serializer.data, status=200)