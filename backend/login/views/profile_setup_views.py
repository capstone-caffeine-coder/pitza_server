# login/views/profile_setup_views.py

from django.contrib.auth import get_user_model
# Removed 'redirect', 'render' as they are not used for the API response part
# from django.shortcuts import redirect, render # Keep redirect if you need it for GET
from django.shortcuts import redirect # Keep redirect if you need it for GET
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist, ValidationError # Keep for potential model validation/lookup
from datetime import date, datetime # For date parsing (less needed with serializer)
import json # Needed for manually decoding if not using DRF's parsers fully, though request.data handles most

# --- Import necessary components from Django REST Framework ---
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status # Needed for HTTP status codes (e.g., status.HTTP_200_OK)
from rest_framework import serializers # Import serializers module

# --- Import necessary components from drf_yasg ---
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# --- Import your serializers ---
from login.serializers import ProfileSetupRequestSerializer, ProfileSetupResponseSerializer


User = get_user_model() # Use get_user_model() or import your custom User model


# --- drf-yasg schemas (can simplify by referencing serializers) ---

# Schema for the POST request body (reference the serializer)
# drf-yasg can often infer this, but explicit linking is good
request_body_schema_profile_setup = ProfileSetupRequestSerializer

# Schema for the successful 200 OK response body (reference the serializer)
success_response_schema = ProfileSetupResponseSerializer

# Schema for common error responses (keep as these are not tied to a specific model/serializer)
error_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'error': openapi.Schema(type=openapi.TYPE_STRING, description="Error message"),
        # The 'errors' structure from DRF serializers
        'errors': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            additionalProperties={'type': 'array', 'items': {'type': 'string'}},
            description="Detailed validation errors per field (if status is 400)",
            nullable=True
        )
    },
    example={'error': 'Validation failed', 'errors': {'nickname': ['This field is required.']}} # Example for 400
)

# Schema for the 302 Redirect response (reusing your definition)
# Keeping this as the GET behavior remains a redirect
redirect_response_schema = openapi.Response(
    description='Redirect to another page.',
    headers={
        'Location': {
            'description': 'The URL to redirect to.',
            'schema': {'type': 'string'}
        }
    }
)


# --- Apply separate swagger_auto_schema decorators for each method ---

# Documentation for the GET method (remains a redirect)
@swagger_auto_schema(
    method='get', # Document only the GET method
    responses={
        '302': redirect_response_schema, # Document the 302 redirect for GET
        '401': openapi.Response('Unauthorized', error_response_schema), # Document if authentication fails
    },
    summary="Initiate Profile Setup Page Load",
    operation_description="Endpoint for loading the client-side profile setup page (performs a redirect). This method is typically for browser navigation, not API calls.",
)
# Documentation for the POST method (NOW returns JSON responses using serializers)
@swagger_auto_schema(
    method='post', # Document only the POST method
    request_body=request_body_schema_profile_setup, # Link request body serializer
    responses={
        '200': openapi.Response('Profile updated successfully', success_response_schema), # Link success response serializer
        '400': openapi.Response('Bad Request - Validation Errors', error_response_schema), # Document validation errors or invalid body
        '401': openapi.Response('Unauthorized', error_response_schema), # Document if user is not authenticated/found
        '404': openapi.Response('User Not Found', error_response_schema), # Document if user ID from session doesn't match DB user
        '500': openapi.Response('Internal Server Error', error_response_schema), # Document unexpected errors
    },
    summary="Submit Profile Setup/Update Data (API)",
    operation_description="Endpoint for submitting user profile data via JSON payload. Returns JSON success or error using serializers.",
)
# --- Decorate with @api_view to make it a DRF view ---
# Allow both GET and POST methods
@api_view(['GET', 'POST'])
@csrf_exempt # Use carefully. Consider other security measures if applicable.
# @login_required # You might want to keep or add @login_required if not using session check explicitly
def profile_setup(request):
    """
    Handles GET to initiate profile setup page (redirect)
    and POST to save profile data via API (returns JSON).
    Uses DRF Serializers for data handling and validation.
    """

    # --- AUTHENTICATION & USER LOOKUP (Using your existing session logic) ---
    # This logic seems custom based on your session handling.
    # You might consider using DRF's Authentication classes instead in a pure API context.
    # Keeping your current session-based lookup for consistency with original code.
    user_id_from_session = request.session.get('user') # Get the stored identifier

    user = None
    if user_id_from_session: # Only attempt lookup if user_id exists in session
        try:
            if isinstance(user_id_from_session, int): # Check if it's already the integer PK
                 user = User.objects.get(pk=user_id_from_session)
            elif isinstance(user_id_from_session, str) and user_id_from_session.startswith("카카오:"): # Handle Kakao prefix
                 kakao_id = user_id_from_session.split(":", 1)[1]
                 user = User.objects.get(kakao_id=kakao_id) # Use get for 404 exception
            elif isinstance(user_id_from_session, str) and '@' in user_id_from_session: # Assume email format
                 user = User.objects.get(email=user_id_from_session) # Use get for 404 exception
            else: # Handle unexpected session identifier format
                 print(f"Unexpected session identifier format: {user_id_from_session}")
                 # Fall through to user is None

        except ObjectDoesNotExist:
            # user_id was in session but user not found in DB
            print(f"User ID/Identifier from session ({user_id_from_session}) not found in DB.")
            # Fall through to user is None

    # If user is not found via the session identifier, return 401 or 404 depending on context
    # If using @login_required, it would handle the 401.
    # If relying solely on your session check:
    if not user:
        print("Authentication failed: User not found via session identifier.")
        return Response({"error": "Authentication failed: User not identified or found."}, status=status.HTTP_401_UNAUTHORIZED)


    # --- POST Request Handling (API Behavior) ---
    if request.method == 'POST':
        # Use the serializer for deserialization and validation
        serializer = ProfileSetupRequestSerializer(instance=user, data=request.data, partial=True) # use partial=True for partial updates

        # Validate the incoming data
        if serializer.is_valid():
            # Data is valid, save the changes to the user instance
            # serializer.save() handles updating the instance passed in `instance=`
            try:
                serializer.save() # This saves the user instance with validated data
                user.refresh_from_db() # Refresh the instance to get the latest data if needed
            except ValidationError as e:
                 # Catch model-level validation errors if any after serializer validation
                 print(f"Model validation error during save for user {user.id}: {e}")
                 return Response({"error": "Model validation failed", "errors": e.message_dict}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                 # Catch other potential database save errors
                 print(f"Database save error for user {user.id}: {e}")
                 return Response({"error": "Could not save profile data due to a server error."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


            # --- Return Success Response (200 OK) ---
            # Use the response serializer to format the output
            response_serializer = ProfileSetupResponseSerializer(instance=user)
            response_data = response_serializer.data
            response_data['message'] = 'Profile updated successfully' # Add the custom message

            return Response(response_data, status=status.HTTP_200_OK)
        else:
            # Data is invalid, return 400 with validation errors
            return Response({"error": "Validation failed", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    # --- GET Request Handling (Original Redirect Behavior) ---
    # This part remains unchanged as you only wanted to modify POST
    # It redirects to the frontend profile setup page.
    # If you wanted a GET API to *retrieve* profile data, you'd add a new view for that.

    print("Received GET request to profile_setup_view. Redirecting to frontend.")
    # Make sure you have imported `redirect` from django.shortcuts if you keep this line
    return redirect('http://localhost:5173/profile/setup/')