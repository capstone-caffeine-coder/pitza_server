# login/views/profile_setup_views.py

from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from datetime import date, datetime
import json

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

import time
from django.shortcuts import redirect

User = get_user_model()

# Schema for the POST request body
request_body_schema_profile_setup = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'nickname': openapi.Schema(type=openapi.TYPE_STRING, description="User's chosen nickname."),
        'birthdate': openapi.Schema(type=openapi.TYPE_STRING, format='date', description="User's birth date (YYYY-MM-DD)."),
        'sex': openapi.Schema(type=openapi.TYPE_STRING, description="User's sex."),
        'blood_type': openapi.Schema(type=openapi.TYPE_STRING, description="User's blood type."),
        'profile_picture': openapi.Schema(type=openapi.TYPE_STRING, description="URL or path to the profile picture.", nullable=True, default=''),
    },
    required=['nickname', 'birthdate', 'sex', 'blood_type']
)

# Schema for the 200 OK response
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

# Schema for error responses
error_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'error': openapi.Schema(type=openapi.TYPE_STRING, description="Error message"),
        'errors': openapi.Schema(type=openapi.TYPE_OBJECT, additionalProperties={'type': 'array', 'items': {'type': 'string'}}, description="Detailed validation errors", nullable=True)
    },
    example={'error': 'Missing required fields', 'errors': {'nickname': ['This field is required.']}}
)

# Schema for 302 redirect
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
    method='get',
    responses={
        '302': redirect_response_schema,
        '401': 'Unauthorized - User not authenticated',
    },
    summary="Initiate Profile Setup Page Load",
    operation_description="Endpoint for loading the client-side profile setup page (redirect)."
)
@swagger_auto_schema(
    method='post',
    request_body=request_body_schema_profile_setup,
    responses={
        '200': openapi.Response('Profile updated successfully', success_response_schema),
        '400': openapi.Response('Bad Request', error_response_schema),
        '401': openapi.Response('Unauthorized', error_response_schema),
        '404': openapi.Response('User Not Found', error_response_schema),
        '500': openapi.Response('Internal Server Error', error_response_schema),
    },
    summary="Submit Profile Setup/Update Data (API)",
    operation_description="Submit user profile data via JSON. Returns success or error response."
)
@api_view(['GET', 'POST'])
@csrf_exempt
def profile_setup(request):
    print(f"DEBUG: profile_setup view received request. Method: {request.method}")
    session_key = request.session.session_key
    print(f"DEBUG: Session Key: {session_key}")
    user_id_from_session = request.session.get('user')
    print(f"DEBUG: 'user' from session: {user_id_from_session}, Type: {type(user_id_from_session)}")
    user = None

    if user_id_from_session:
        time.sleep(0.5)

        try:
            if isinstance(user_id_from_session, int):
                user = User.objects.get(pk=user_id_from_session)
            elif user_id_from_session.startswith("카카오:"):
                kakao_id = user_id_from_session.split(":", 1)[1]
                user = User.objects.get(kakao_id=kakao_id)
            else:
                user = User.objects.get(email=user_id_from_session)
        except ObjectDoesNotExist:
            print(f"User ID/Identifier from session ({user_id_from_session}) not found in DB.")
            if isinstance(user_id_from_session, int):
                print(f"User ID {user_id_from_session} from session {session_key} not found in database.")

    if not user:
        print("Authentication failed: User not found via session identifier.")
        return Response({"error": "Authentication failed: User not identified."}, status=status.HTTP_401_UNAUTHORIZED)

    if request.method == 'POST':
        data = request.data
        errors = {}
        nickname = data.get('nickname')
        birthdate_str = data.get('birthdate')
        sex = data.get('sex')
        blood_type = data.get('blood_type')
        profile_picture = data.get('profile_picture', '')

        if not nickname:
            errors['nickname'] = ['This field is required.']
        elif len(nickname) > 100:
            errors['nickname'] = ['Nickname cannot exceed 100 characters.']

        birthdate = None
        if birthdate_str:
            try:
                birthdate = datetime.strptime(birthdate_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                errors['birthdate'] = ['Invalid date format. Use YYYY-MM-DD.']

        if not sex:
            errors['sex'] = ['This field is required.']

        if errors:
            return Response({"error": "Validation failed", "errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        if 'nickname' in data: user.nickname = nickname
        if 'birthdate' in data: user.birthdate = birthdate
        if 'sex' in data: user.sex = sex
        if 'blood_type' in data: user.blood_type = blood_type
        if 'profile_picture' in data: user.profile_picture = profile_picture

        try:
            user.full_clean()
            user.save()
        except ValidationError as e:
            return Response({"error": "Model validation failed", "errors": e.message_dict}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"Error saving user profile for user {user.id}: {e}")
            return Response({"error": "Could not save profile data"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        success_data = {
            'id': user.id,
            'email': user.email,
            'kakao_id': user.kakao_id,
            'nickname': user.nickname,
            'profile_picture': user.profile_picture,
            'message': 'Profile updated successfully',
        }

        return Response(success_data, status=status.HTTP_200_OK)

    print("Received GET request to profile_setup_view. Redirecting to frontend.")
    from django.shortcuts import redirect
    return redirect('http://localhost:5173/profile/setup/')
