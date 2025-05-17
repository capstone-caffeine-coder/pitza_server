from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User  # or your custom user model
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import serializers
from login.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'kakao_id', 'nickname','birthdate', 'sex', 'blood_type', 'profile_picture', 'age']
        
        
@api_view(['GET'])
@swagger_auto_schema(responses={200: 'User details retrieved successfully'})
def user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    serializer = UserSerializer(user)

    return Response(serializer.data, status=200)
