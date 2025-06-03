from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

User = get_user_model()

@swagger_auto_schema(
    method='get',
    responses={
        status.HTTP_200_OK: openapi.Response(
            description='User details retrieved successfully. Includes profile completeness status.',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'id': openapi.Schema(type=openapi.TYPE_INTEGER, description="The user's primary key."),
                    'email': openapi.Schema(type=openapi.TYPE_STRING, format='email', nullable=True, description="The user's email address (if available)."),
                    'kakao_id': openapi.Schema(type=openapi.TYPE_STRING, nullable=True, description="The user's Kakao ID (if available)."),
                    'nickname': openapi.Schema(type=openapi.TYPE_STRING, nullable=True, description="The user's nickname."),
                    'is_profile_complete': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Indicates if basic profile fields are complete."),
                }
            )
        ),
        status.HTTP_401_UNAUTHORIZED: 'Unauthorized - User is not authenticated.',
    },
    summary="Get Current User Profile Status (Function-Based)",
    operation_description="API endpoint to get the currently logged-in user's basic info and profile completeness. Requires authentication."
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_by_session_api(request):
    user = request.user

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