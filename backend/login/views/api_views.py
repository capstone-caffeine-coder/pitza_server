
from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
# csrf_exempt might still be needed if you're not using DRF's authentication/CSRF handling,
# but @api_view often provides its own handling depending on settings.
# For simplicity here, we'll keep csrf_exempt, but consider DRF auth/permissions in production.
from django.views.decorators.csrf import csrf_exempt

# --- Import necessary components from Django REST Framework ---
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status # Recommended way to use HTTP status codes in DRF

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi # Needed to manually define schemas

# from login.models import User # <-- Make sure this is correctly imported if not using get_user_model() returning your custom model

User = get_user_model() # Use get_user_model() to get the active user model

# --- Define the schema for the expected request body ---
# This describes the JSON structure {"session_key": "..."}
request_body_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'session_key': openapi.Schema(
            type=openapi.TYPE_STRING,
            description="The Django session key.",
            example="abcdefghijklmnopqrstuvwxyz123456" # Example session key
        )
    },
    required=['session_key']
)

# --- Define the schema for the 200 OK response body ---
# This describes the JSON structure of the user info returned
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
    method='post', # Specify the method for documentation
    request_body=request_body_schema, # Link the request body schema
    responses={
        # Link the response body schema for 200 OK
        status.HTTP_200_OK: openapi.Response(
            description='User details retrieved successfully. Includes profile completeness status.',
            schema=user_info_response_schema
        ),
        status.HTTP_400_BAD_REQUEST: 'Bad Request - Invalid JSON, missing session_key, or invalid session key format.',
        status.HTTP_401_UNAUTHORIZED: 'Unauthorized - Session is valid but does not contain a logged-in user.',
        status.HTTP_403_FORBIDDEN: 'Forbidden - Session has expired.',
        status.HTTP_404_NOT_FOUND: 'Not Found - Session key does not exist, or user ID found in session does not correspond to an existing user.',
        status.HTTP_405_METHOD_NOT_ALLOWED: 'Method Not Allowed - If the request method is not POST.',
        status.HTTP_500_INTERNAL_SERVER_ERROR: 'Internal Server Error - An unexpected error occurred.',
    },
    summary="Get User Details by Session Key",
    operation_description="API endpoint to get user info based on session key. Expects a POST request with JSON body.",
)
# --- Decorate with @api_view to make it a DRF view ---
@api_view(['POST'])
@csrf_exempt # Keep csrf_exempt if needed, but review DRF authentication/permissions
def get_user_by_session_api(request):


    # DRF's @api_view handles method checking, but an explicit check is fine too
    # if request.method != 'POST': # No longer strictly needed with @api_view(['POST'])
    #    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED) # Use DRF status

    try:
        # Access data using request.data (DRF parses JSON/form data)
        # DRF handles JSONDecodeError and basic malformed data
        data = request.data
        session_key = data.get('session_key')

        if not session_key:
            return Response({"error": "Missing 'session_key' in request body"}, status=status.HTTP_400_BAD_REQUEST)

        # Basic validation: Django session keys are usually 32 characters
        if len(session_key) != 32: # Note: This length can vary if you change SESSION_ENGINE or its configuration
             return Response({"error": "Invalid session key format"}, status=status.HTTP_400_BAD_REQUEST)

        # --- Session Validation and User Retrieval ---
        session = None
        try:
            session = Session.objects.get(session_key=session_key)
        except ObjectDoesNotExist:
            print(f"Session key not found: {session_key}") # Log this server-side
            return Response({"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND)

        # Check if the session has expired
        if session.expire_date < timezone.now():
             print(f"Session expired: {session_key}") # Log this server-side
             # Optionally delete the expired session here
             # session.delete()
             return Response({"error": "Session expired"}, status=status.HTTP_403_FORBIDDEN)

        # Get the decoded session data
        session_data = session.get_decoded()

        # Get the user ID from the session data
        user_id = session_data.get('_auth_user_id')

        # --- Handle Not Logged In via Session (Requested 401) ---
        if not user_id:
            print(f"Session {session_key} does not contain a logged-in user.") # Log this
            # Return 401 Unauthorized using DRF Response and status
            return Response({"error": "Unauthorized - Session does not contain a logged-in user"}, status=status.HTTP_401_UNAUTHORIZED)

        # --- User IS Logged In - Proceed to Get User Object ---
        user = None
        try:
            user = User.objects.get(pk=user_id)
        except ObjectDoesNotExist:
             print(f"User ID {user_id} from session {session_key} not found.") # Log this
             # Optionally delete the invalid session here
             # session.delete()
             return Response({"error": "User not found for this session"}, status=status.HTTP_404_NOT_FOUND)


        # --- User Found - Return User Information and Profile Completeness ---
        # Check if basic profile information is complete
        # Assuming basic fields are nickname, birthdate, sex, blood_type from profile_setup
        is_profile_complete = bool(
            getattr(user, 'nickname', None) and
            getattr(user, 'birthdate', None) is not None and # Check date field is not None
            getattr(user, 'sex', None) and
            getattr(user, 'blood_type', None)
        )

        # Build the user data dictionary
        user_info = {
            'id': user.id,
            'email': getattr(user, 'email', None),
            'kakao_id': getattr(user, 'kakao_id', None),
            'nickname': getattr(user, 'nickname', None),
            'is_profile_complete': is_profile_complete,
        }

        # Return the JsonResponse using DRF Response
        return Response(user_info, status=status.HTTP_200_OK)

    except Exception as e:
        # Catch any other unexpected errors during the process
        print(f"An unexpected error occurred in get_user_by_session_api: {e}") # Log the full error
        return Response({'error': 'An internal server error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)