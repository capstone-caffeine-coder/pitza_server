from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import routers


from login import views
from login.views.auth_views import login_view, login_google, google_callback, login_kakao, kakao_callback
from login.views.user_views import user_detail
from login.views.api_views import get_user_by_session_api
from donations.views import DonationRequestViewSet
from login.views.profile_setup_views import UserProfileSetupView, profile_setup_redirect


schema_view = get_schema_view(
   openapi.Info(
      title="Pitza API",
      default_version='v1',
      description="This is the API documentation for the Pitza project.",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

router = routers.SimpleRouter()
router.register(r'donations', DonationRequestViewSet, basename='donations')


urlpatterns = [
   # swagger
   path('swagger.<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
   path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
   path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
   # project
   path('admin/', admin.site.urls),
   path('chat/', include('chat.urls')),
   path("services/", include("services.urls")),
  
   # Auth views
   path('', login_view, name='login'),
   path('login/google/', login_google, name='login_google'),
   path('oauth/google/callback/', google_callback, name='google_callback'),
   path('login/kakao/', login_kakao, name='login_kakao'),
   path('oauth/kakao/callback/', kakao_callback, name='kakao_callback'),

   # User info view
   path('user/<int:pk>/', user_detail, name='user_detail'),

   path('', include('board.urls')),
   
   # API views
   path('get_user_by_session/', get_user_by_session_api, name='get_user_by_session_api'),

   # userprofile
   path('profile/setup/', UserProfileSetupView.as_view(), name='profile-setup'),
   path('profile/setup/redirect/', profile_setup_redirect, name='profile-setup-redirect-get'),
]

urlpatterns += router.urls