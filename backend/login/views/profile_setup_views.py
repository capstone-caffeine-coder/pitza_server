# login/views/profile_setup_views.py

from django.contrib.auth import get_user_model
# Removed 'redirect', 'render' as they are not used for the API response part
# from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from datetime import date, datetime # For date parsing
import json # Needed for manually decoding if not using DRF's parsers fully, though request.data handles most

# --- Import necessary components from Django REST Framework ---
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status # Needed for HTTP status codes (e.g., status.HTTP_200_OK)

# --- Import necessary components from drf_yasg ---
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

User = get_user_model() # Use get_user_model() or import your custom User model


# --- Define schemas for request body (POST) and responses ---

# Schema for the POST request body (expecting JSON data now)
request_body_schema_profile_setup = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'nickname': openapi.Schema(type=openapi.TYPE_STRING, description="User's chosen nickname."),
        'birthdate': openapi.Schema(type=openapi.TYPE_STRING, format='date', description="User's birth date (YYYY-MM-DD)."),
        'sex': openapi.Schema(type=openapi.TYPE_STRING, description="User's sex."), # Consider using choices/enum if applicable
        'blood_type': openapi.Schema(type=openapi.TYPE_STRING, description="User's blood type."), # Consider using choices/enum if applicable
        'profile_picture': openapi.Schema(type=openapi.TYPE_STRING, description="URL or path to the profile picture.", nullable=True, default=''),
    },
    # Mark fields as required if your validation checks enforce this
    required=['nickname', 'birthdate', 'sex', 'blood_type'] # Adjust based on actual required fields
)

# Schema for the successful 200 OK response body
success_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        # Define the structure of the JSON you return on success
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description="User ID"),
        'email': openapi.Schema(type=openapi.TYPE_STRING, format='email', description="User email (if applicable)", nullable=True),
        'kakao_id': openapi.Schema(type=openapi.TYPE_STRING, description="User Kakao ID (if applicable)", nullable=True),
        'nickname': openapi.Schema(type=openapi.TYPE_STRING, description="Updated nickname"),
        'profile_picture': openapi.Schema(type=openapi.TYPE_STRING, description="Updated profile picture URL", nullable=True),
        'message': openapi.Schema(type=openapi.TYPE_STRING, description="Success message"),
        # Add other fields returned on success
    },
    example={ # Provide an example of the successful response
        'id': 123,
        'email': 'user@example.com',
        'kakao_id': None,
        'nickname': 'NewNickname',
        'profile_picture': 'http://example.com/pic.jpg',
        'message': 'Profile updated successfully',
    }
)

# Schema for common error responses (e.g., 400, 401, 404, 500)
error_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'error': openapi.Schema(type=openapi.TYPE_STRING, description="Error message"),
        # Optionally include a 'details' field for validation errors
        'errors': openapi.Schema(type=openapi.TYPE_OBJECT, additionalProperties={'type': 'array', 'items': {'type': 'string'}}, description="Detailed validation errors per field", nullable=True)
    },
    example={'error': 'Missing required fields', 'errors': {'nickname': ['This field is required.']}} # Example for 400
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
        '401': 'Unauthorized - User not authenticated', # Document if @login_required fails
    },
    summary="Initiate Profile Setup Page Load",
    operation_description="Endpoint for loading the client-side profile setup page (performs a redirect). This method is typically for browser navigation, not API calls.",
)
# Documentation for the POST method (NOW returns JSON responses)
@swagger_auto_schema(
    method='post', # Document only the POST method
    request_body=request_body_schema_profile_setup, # Link request body schema
    responses={
        '200': openapi.Response('Profile updated successfully', success_response_schema), # Document the new 200 success response
        '400': openapi.Response('Bad Request', error_response_schema), # Document validation errors or invalid body
        '401': openapi.Response('Unauthorized', error_response_schema), # Document if user is not authenticated/found
        '404': openapi.Response('User Not Found', error_response_schema), # Document if user ID from session doesn't match DB user
        '500': openapi.Response('Internal Server Error', error_response_schema), # Document unexpected errors
    },
    summary="Submit Profile Setup/Update Data (API)",
    operation_description="Endpoint for submitting user profile data via JSON payload. Returns JSON success or error.",
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
    """

    # --- AUTHENTICATION & USER LOOKUP (Using your existing session logic) ---
    # This logic seems custom based on your session handling
    # You might consider using DRF's Authentication classes instead in a pure API context,
    # but keeping your current session-based lookup for consistency.
    user_id_from_session = request.session.get('user') # Get the stored identifier

    user = None
    if user_id_from_session: # Only attempt lookup if user_id exists in session
        try:
            if isinstance(user_id_from_session, int): # Check if it's already the integer PK
                 user = User.objects.get(pk=user_id_from_session)
            elif user_id_from_session.startswith("카카오:"): # Handle Kakao prefix
                kakao_id = user_id_from_session.split(":", 1)[1]
                user = User.objects.get(kakao_id=kakao_id) # Use get, not filter().first() for 404 exception
            else: # Assume email or another identifier format
                user = User.objects.get(email=user_id_from_session) # Use get, not filter().first()

        except ObjectDoesNotExist:
            # user_id was in session but user not found in DB
            print(f"User ID/Identifier from session ({user_id_from_session}) not found in DB.")
            # Fall through to user is None

    # If user is not found via the session identifier, return 401 or 404 depending on context
    # If using @login_required, it would handle the 401.
    # If relying solely on your session check:
    if not user:
        print("Authentication failed: User not found via session identifier.")
        return Response({"error": "Authentication failed: User not identified."}, status=status.HTTP_401_UNAUTHORIZED)


    # --- POST Request Handling (API Behavior) ---
    if request.method == 'POST':
        # request.data automatically handles JSON if Content-Type is application/json
        data = request.data

        # --- Extract and Validate Data ---
        # You can add more robust validation here.
        # Consider using a DRF Serializer for complex validation and data handling.
        errors = {}
        nickname = data.get('nickname')
        birthdate_str = data.get('birthdate')
        sex = data.get('sex')
        blood_type = data.get('blood_type')
        profile_picture = data.get('profile_picture', '') # Default to empty string if not provided

        # Manual validation examples (more comprehensive validation might be needed)
        if not nickname:
             errors['nickname'] = ['This field is required.']
        elif len(nickname) > 100:
             errors['nickname'] = ['Nickname cannot exceed 100 characters.']

        birthdate = None
        if birthdate_str:
            try:
                # Attempt to parse date string
                birthdate = datetime.strptime(birthdate_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                 errors['birthdate'] = ['Invalid date format. Use YYYY-MM-DD.']
        # else:
        #      errors['birthdate'] = ['This field is required.'] # Uncomment if birthdate is required

        if not sex:
             errors['sex'] = ['This field is required.']
        # Add validation for sex and blood_type based on allowed choices

        if errors:
            # Return 400 Bad Request with validation errors
            return Response({"error": "Validation failed", "errors": errors}, status=status.HTTP_400_BAD_REQUEST)


        # --- Apply Validated Data to User Model ---
        # Only update fields if the corresponding key was present in the request data
        # Use `data.get('field') is not None` if field could be required but empty string allowed
        if 'nickname' in data: user.nickname = nickname
        if 'birthdate' in data: user.birthdate = birthdate # birthdate is None if parsing failed
        if 'sex' in data: user.sex = sex
        if 'blood_type' in data: user.blood_type = blood_type
        if 'profile_picture' in data: user.profile_picture = profile_picture # Allows setting to '' or None

        try:
            user.full_clean() # Run model validation (defined in your models.py if any)
            user.save()
        except ValidationError as e:
             # Catch model-level validation errors if any
             return Response({"error": "Model validation failed", "errors": e.message_dict}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
             # Catch other potential save errors
             print(f"Error saving user profile for user {user.id}: {e}")
             return Response({"error": "Could not save profile data"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        # --- Return Success Response (200 OK) ---
        # Construct the response body you want to send back on success
        success_data = {
            'id': user.id,
            'email': user.email,
            'kakao_id': user.kakao_id,
            'nickname': user.nickname,
            'profile_picture': user.profile_picture,
            'message': 'Profile updated successfully',
            # Add other fields you want to confirm were saved or send back
            # 'age': user.age if user.birthdate else None,
        }

        return Response(success_data, status=status.HTTP_200_OK)

    # --- GET Request Handling (Original Redirect Behavior) ---
    # This part remains unchanged as you only wanted to modify POST
    # It redirects to the frontend profile setup page.
    # If you wanted a GET API to *retrieve* profile data, you'd add a new view for that.

    print("Received GET request to profile_setup_view. Redirecting to frontend.")
    # Make sure you have imported `redirect` from django.shortcuts if you keep this line
    from django.shortcuts import redirect
    return redirect('http://localhost:5173/profile/setup/')