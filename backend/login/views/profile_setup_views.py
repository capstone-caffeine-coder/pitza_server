# login/views/profile_setup_views.py

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from datetime import date, datetime
import json
import uuid
import requests
from io import BytesIO

from rest_framework import generics, permissions, parsers
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from login.models import User
from login.serializers import UserProfileSerializer
from django.shortcuts import redirect



User = get_user_model()


class UserProfileSetupView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def get_object(self):
        return self.request.user
    
    def post(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)



request_body_schema_profile_setup = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'nickname': openapi.Schema(type=openapi.TYPE_STRING, description="User's chosen nickname."),
        'birthdate': openapi.Schema(type=openapi.TYPE_STRING, format='date', description="User's birth date (YYYY-MM-DD)."),
        'sex': openapi.Schema(type=openapi.TYPE_STRING, description="User's sex."),
        'blood_type': openapi.Schema(type=openapi.TYPE_STRING, description="User's blood type."),
        'profile_picture_input': openapi.Schema(type=openapi.TYPE_STRING, description="A URL to a remote profile picture to download and store, or an empty string to clear.", nullable=True),
        'profile_picture_file': openapi.Schema(type=openapi.TYPE_FILE, description="An uploaded image file for the profile picture.", nullable=True),
    },
    required=['nickname', 'birthdate', 'sex', 'blood_type']
)

success_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description="User ID"),
        'email': openapi.Schema(type=openapi.TYPE_STRING, format='email', description="User email", nullable=True),
        'kakao_id': openapi.Schema(type=openapi.TYPE_STRING, description="User Kakao ID", nullable=True),
        'nickname': openapi.Schema(type=openapi.TYPE_STRING, description="Updated nickname"),
        'profile_picture': openapi.Schema(type=openapi.TYPE_STRING, description="Updated profile picture URL", nullable=True),
        'message': openapi.Schema(type=openapi.TYPE_STRING, description="Success message"),
    },
    example={
        'id': 123,
        'email': 'user@example.com',
        'kakao_id': None,
        'nickname': 'NewNickname',
        'profile_picture': 'http://example.com/pic.jpg',
        'message': 'Profile updated successfully',
    }
)

error_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'error': openapi.Schema(type=openapi.TYPE_STRING, description="Error message"),
        'errors': openapi.Schema(type=openapi.TYPE_OBJECT, additionalProperties={'type': 'array', 'items': {'type': 'string'}}, description="Detailed validation errors", nullable=True)
    },
    example={'error': 'Missing required fields', 'errors': {'nickname': ['This field is required.']}}
)

redirect_response_schema = openapi.Response(
    description='Redirect to another page.',
    headers={
        'Location': {
            'description': 'The URL to redirect to.',
            'schema': {'type': 'string'}
        }
    }
)


@swagger_auto_schema(
    method='post',
    responses={
        '302': redirect_response_schema,
        '401': 'Unauthorized - User not authenticated',
    },
    summary="Initiate Profile Setup Page Load",
    operation_description="Endpoint for loading the client-side profile setup page (redirect)."
)
@api_view(['POST'])
def profile_setup_redirect(request):
    user_id_from_session = request.session.get('user')
    user = None

    if user_id_from_session:
        try:
            if isinstance(user_id_from_session, int):
                user = User.objects.get(pk=user_id_from_session)
            elif user_id_from_session.startswith("카카오:"):
                kakao_id = user_id_from_session.split(":", 1)[1]
                user = User.objects.get(kakao_id=kakao_id)
            else:
                user = User.objects.get(email=user_id_from_session)
        except ObjectDoesNotExist:
            pass

    if not user:
        return Response({"error": "Authentication failed: User not identified."}, status=status.HTTP_401_UNAUTHORIZED)

    return redirect('http://localhost:5173/profile/setup/')