from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from login.serializers import UserProfileSerializer

User = get_user_model()

@swagger_auto_schema(
    method='get',
    responses={
        status.HTTP_200_OK: openapi.Response(
            description='User details retrieved successfully. Includes profile completeness status and profile picture.',
            schema=UserProfileSerializer
        ),
        status.HTTP_401_UNAUTHORIZED: 'Unauthorized - User is not authenticated.',
    },
    summary="Get Current User Profile Status (Function-Based)",
    operation_description="API endpoint to get the currently logged-in user's basic info, profile completeness, and profile picture. Requires authentication."
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_by_session_api(request):
    user = request.user

    serializer = UserProfileSerializer(user)

    is_profile_complete = bool(
        getattr(user, 'nickname', None) and
        getattr(user, 'birthdate', None) is not None and
        getattr(user, 'sex', None) and
        getattr(user, 'blood_type', None)
    )


    response_data = serializer.data.copy()


    response_data['is_profile_complete'] = is_profile_complete

    return Response(response_data, status=status.HTTP_200_OK)