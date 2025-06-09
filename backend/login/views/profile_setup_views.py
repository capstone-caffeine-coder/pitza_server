from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from datetime import date, datetime
import json

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework.request import Request 

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from login.models import User
from login.serializers import UserProfileSerializer
from django.shortcuts import redirect


User = get_user_model()

# --- Schema Definitions (as in previous corrected version) ---
redirect_response_schema = openapi.Response(
    description='Redirect to another page.',
    headers={
        'Location': {
            'description': 'The URL to redirect to.',
            'schema': {'type': 'string'}
        }
    }
)

# --- UserProfileSetupView (with Debugging Prints) ---
class UserProfileSetupView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser] 

    def get_object(self):
        # --- DEBUGGING PRINT ---
        print(f"DEBUG: In get_object() method.")
        print(f"DEBUG: self.request.user: {self.request.user}")
        print(f"DEBUG: Is self.request.user authenticated? {self.request.user.is_authenticated}")
        
        # Ensure that request.user is an authenticated User instance.
        # permissions.IsAuthenticated should handle this, but this helps confirm.
        if not self.request.user or not self.request.user.is_authenticated:
            print("DEBUG: get_object() found unauthenticated or invalid user. Raising NotAuthenticated.")
            raise permissions.NotAuthenticated("Authentication credentials were not provided or are invalid.")
        
        # If user is authenticated and valid, return it as the instance for the serializer.
        return self.request.user
    
    def post(self, request: Request, *args, **kwargs):
        # --- DEBUGGING PRINTS ---
        print(f"DEBUG: In UserProfileSetupView POST method.")
        print(f"DEBUG: Request user: {request.user}")
        print(f"DEBUG: Is request.user authenticated? {request.user.is_authenticated}")
        print(f"DEBUG: Request data received: {request.data}")
        print(f"DEBUG: Type of request data: {type(request.data)}")

        try:
            # This calls the partial_update method of the base RetrieveUpdateAPIView.
            # partial_update internally calls get_serializer, passing instance=self.get_object() and data=request.data.
            response = self.partial_update(request, *args, **kwargs)
            print(f"DEBUG: partial_update completed with status: {response.status_code}")
            return response
        except Exception as e:
            # --- DEBUGGING PRINT ---
            print(f"DEBUG: An unexpected error occurred during partial_update: {type(e).__name__}: {e}")
            # Re-raise the exception to see the full traceback in your console
            raise 


# --- profile_setup_redirect (as in previous corrected version) ---
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
def profile_setup_redirect(request: Request):
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