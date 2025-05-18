from django.contrib.sessions.models import Session
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
# csrf_exempt might still be needed depending on your DRF settings and authentication setup.
# If using DRF's SessionAuthentication, you might not need it here.
from django.views.decorators.csrf import csrf_exempt

# --- Import necessary components from Django REST Framework ---
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status # Recommended way to use HTTP status codes in DRF
# You don't need SerializerValidationError if you're not using a request serializer that raises it


# --- Import necessary components from drf_yasg ---
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi # Needed to manually define schemas

# --- Import your new serializers ---
# Adjust the import path if your serializers.py is not in the same directory
# We only need the Response Serializer for this minimal change
from login.serializers import UserInfoResponseSerializer


User = get_user_model() # Use get_user_model() to get the active user model

# --- Define the schema for the expected request body (Keeping your manual definition) ---
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

# --- Define the schema for the 200 OK response body (Referencing the Serializer for Swagger) ---
# This describes the JSON structure of the user info returned
user_info_response_schema = UserInfoResponseSerializer # Link the serializer class here for Swagger


@swagger_auto_schema(
    method='post', # Specify the method for documentation
    request_body=request_body_schema, # Link the request body schema (your manual one)
    responses={
        # Link the response body schema for 200 OK (Referencing the Serializer)
        status.HTTP_200_OK: openapi.Response(
            description='User details retrieved successfully. Includes profile completeness status.',
            schema=user_info_response_schema # Use the serializer class here
        ),
        # Keeping your manual error descriptions or use a generic error schema
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
@csrf_exempt # Keep csrf_exempt if needed
def get_user_by_session_api(request):
    """
    API endpoint to get user info based on session key.
    Uses DRF Response and status, manual input handling, and a Response Serializer for output.
    """

    # --- Initialize session_key to None ---
    # This helps satisfy linters that might warn about accessing session_key
    # in the final except block if an error occurs before it's assigned.
    session_key = None
    # -------------------------------------

    try:
        # Access data using request.data (DRF parses JSON/form data automatically)
        # DRF handles basic malformed JSON errors, but you're keeping manual validation checks.
        data = request.data
        session_key = data.get('session_key') # session_key is assigned here if data is available

        # --- Your existing manual validation checks ---
        if not session_key:
            return Response({"error": "Missing 'session_key' in request body"}, status=status.HTTP_400_BAD_REQUEST)

        # Basic validation: Django session keys are usually 32 characters
        # Adjust this length check if your SESSION_ENGINE configuration changes it
        if len(session_key) != 32:
             return Response({"error": "Invalid session key format"}, status=status.HTTP_400_BAD_REQUEST)

        # --- Session Validation and User Retrieval ---
        session = None # Initialize session to None
        try:
            session = Session.objects.get(session_key=session_key)
        except ObjectDoesNotExist:
            # Use .format() instead of f-string for compatibility if Python < 3.6
            print("Session key not found: {}".format(session_key)) # Log this server-side
            return Response({"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND)

        # Check if the session has expired
        if session.expire_date < timezone.now():
             # Use .format() instead of f-string for compatibility if Python < 3.6
             print("Session expired: {}".format(session_key)) # Log this server-side
             # Optionally delete the expired session here: session.delete()
             return Response({"error": "Session expired"}, status=status.HTTP_403_FORBIDDEN)

        # Get the decoded session data
        session_data = session.get_decoded()

        # Get the user ID from the session data (standard key used by Django's auth)
        user_id = session_data.get('_auth_user_id')

        # --- Handle Case: Session exists but user is NOT logged in via auth system ---
        if not user_id:
            # Use .format() instead of f-string for compatibility if Python < 3.6
            print("Session {} does not contain a logged-in user ID (_auth_user_id).".format(session_key)) # Log this
            # Return 401 Unauthorized using DRF Response and status
            return Response({"error": "Unauthorized - Session does not contain a logged-in user"}, status=status.HTTP_401_UNAUTHORIZED)

        # --- User IS Logged In via Session - Proceed to Get User Object ---
        user = None # Initialize user to None
        try:
            user = User.objects.get(pk=user_id)
        except ObjectDoesNotExist:
             # Use .format() instead of f-string for compatibility if Python < 3.6
             print("User ID {} from session {} not found in database.".format(user_id, session_key)) # Log this
             # This could happen if a user was deleted but their session wasn't.
             # Optionally delete the invalid session here: session.delete()
             return Response({"error": "User not found for this session"}, status=status.HTTP_404_NOT_FOUND)


        # --- User Found - Prepare and Return User Information using Response Serializer ---
        # Check if basic profile information is complete
        # Adjust these field names ('nickname', 'birthdate', 'sex', 'blood_type')
        # if they are different on your custom User model.
        # Use getattr with default None for safety if these fields might truly not exist
        # on some user objects or in older data.
        is_profile_complete = bool(
            getattr(user, 'nickname', None) and
            getattr(user, 'birthdate', None) is not None and # Check specifically for not None as DateField can be None
            getattr(user, 'sex', None) and
            getattr(user, 'blood_type', None)
            # Add other fields you consider essential for profile completeness
        )

        # Build the user data dictionary (as you did before)
        # This dictionary will be passed to the serializer
        user_info_data = {
            'id': user.id,
            'email': getattr(user, 'email', None),
            'kakao_id': getattr(user, 'kakao_id', None),
            'nickname': getattr(user, 'nickname', None),
            'is_profile_complete': is_profile_complete,
            # Add other user fields you want in the response if needed
        }

        # Use the Response Serializer to format the output data
        # Pass the data dictionary to the serializer instance
        response_serializer = UserInfoResponseSerializer(user_info_data)

        # Return the Response with the serialized data and the 200 OK status
        # The .data attribute contains the serialized dictionary.
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    # --- Catch any unexpected errors during the process ---
    # This block was showing persistent red lines in the image.
    # Linter might show a warning on 'except Exception' - this is common practice
    # as a last resort catch-all for API views, but linters can flag it.
    except Exception as e:
        # Use .format() instead of f-string for compatibility if your Python version is < 3.6
        # The red line on this print statement in the image is unusual if syntax is correct.
        # Check for typos or editor issues on this specific line.
        print("An unexpected error occurred in get_user_by_session_api for session: {}. Error: {}".format(session_key if 'session_key' in locals() else 'N/A', e)) # Log the full error and session key if known

        # Return a generic 500 error response for unexpected server errors.
        # In production, avoid exposing detailed error information for security.
        # --- FIX FOR THE PERSISTENT SYNTAX ERROR RED LINE ---
        # Make sure the status argument is INSIDE the Response() call.
        # The incorrect syntax was return Response(..., ), status=...
        # It MUST be return Response(..., status=...)
        return Response({'error': 'An internal server error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)