from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from login.serializers import UserProfileSerializer
from login.models import User

User = get_user_model()


@api_view(['GET', 'POST', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def profile_setup(request):
    user = request.user

    if request.method == 'GET':
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)

    elif request.method in ['POST', 'PUT', 'PATCH']:
        serializer = UserProfileSerializer(user, data=request.data, partial=True)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)


    return Response({"detail": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

user_info_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description="The user's primary key."),
        'email': openapi.Schema(type=openapi.TYPE_STRING, format='email', nullable=True, description="The user's email address (if available)."),
        'kakao_id': openapi.Schema(type=openapi.TYPE_STRING, nullable=True, description="The user's Kakao ID (if available)."),
        'nickname': openapi.Schema(type=openapi.TYPE_STRING, nullable=True, description="The user's nickname."),
        'is_profile_complete': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Indicates if basic profile fields are complete."),
    }
)

@swagger_auto_schema(
    method='get',
    responses={
        status.HTTP_200_OK: openapi.Response(
            description='User details retrieved successfully. Includes profile completeness status.',
            schema=user_info_response_schema
        ),
        status.HTTP_401_UNAUTHORIZED: 'Unauthorized - User is not authenticated via session cookie, or session does not contain a logged-in user.',
        status.HTTP_403_FORBIDDEN: 'Forbidden - Session has expired or is invalid.',
        status.HTTP_404_NOT_FOUND: 'Not Found - User ID found in session does not correspond to an existing user.',
        status.HTTP_500_INTERNAL_SERVER_ERROR: 'Internal Server Error - An unexpected error occurred.',
    },
    summary="Get Current User Details via Session Cookie",
    operation_description="API endpoint to get the currently logged-in user's info. Expects a GET request where the session key is sent via HTTP cookies. The server verifies the session and retrieves user data.",
)
@api_view(['GET'])
@csrf_exempt
def get_user_by_session_api(request):
    session_key = request.session.session_key

    if not session_key:
        print("No session key found in request cookies.")
        return Response({"error": "Authentication failed - No session cookie provided or valid."}, status=status.HTTP_401_UNAUTHORIZED)

    session = None
    try:
        session = Session.objects.get(session_key=session_key)

        if session.expire_date < timezone.now():
            print("Session expired for key: {}".format(session_key))
            return Response({"error": "Session expired"}, status=status.HTTP_403_FORBIDDEN)

        session_data = session.get_decoded()
        user_id = session_data.get('_auth_user_id')

        if not user_id:
            print("Session {} does not contain a logged-in user ID (_auth_user_id).".format(session_key))
            return Response({"error": "Unauthorized - Session does not contain a logged-in user"}, status=status.HTTP_401_UNAUTHORIZED)

        user = None
        try:
            user = User.objects.get(pk=user_id)
        except ObjectDoesNotExist:
            print("User ID {} from session {} not found in database.".format(user_id, session_key))
            return Response({"error": "User not found for this session"}, status=status.HTTP_404_NOT_FOUND)

        is_profile_complete = bool(
            getattr(user, 'nickname', None) and
            getattr(user, 'birthdate', None) is not None and
            getattr(user, 'sex', None) and
            getattr(user, 'blood_type', None)
        )

        user_info = {
            'id': user.id,
            'email': getattr(user, 'email', None),
            'kakao_id': getattr(user, 'kakao_id', None),
            'nickname': getattr(user, 'nickname', None),
            'is_profile_complete': is_profile_complete,
        }

        return Response(user_info, status=status.HTTP_200_OK)

    except ObjectDoesNotExist:
        print("Session key {} found in cookie but not in database.".format(session_key if session_key else 'N/A'))
        return Response({"error": "Invalid session"}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        print("An unexpected error occurred in get_user_by_session_api for session key: {}. Error: {}".format(session_key if 'session_key' in locals() else 'N/A', e))
        return Response({'error': 'An internal server error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)