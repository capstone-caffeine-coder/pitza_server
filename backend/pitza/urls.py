from django.contrib import admin
from django.urls import path, include
from donations.views import DonationRequestViewSet
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import routers

schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="Test description",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

router = routers.SimpleRouter()
router.register(r'donations', DonationRequestViewSet, basename='donations')
from login import views
from login.views.auth_views import login_view, login_google, google_callback, login_kakao, kakao_callback
from login.views.user_views import user_detail  # Import your user detail view

urlpatterns = [
    # swagger
    path('swagger.<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    # project
    path('admin/', admin.site.urls),
    path('chat/', include('chat.urls')),

    # Auth views
    path('', login_view, name='login'),
    path('login/google/', login_google, name='login_google'),
    path('oauth/google/callback/', google_callback, name='google_callback'),
    path('login/kakao/', login_kakao, name='login_kakao'),
    path('oauth/kakao/callback/', kakao_callback, name='kakao_callback'),
    path('profile/setup/', views.profile_setup, name='profile_setup'),

    # User info view
    path('user/<int:pk>/', user_detail, name='user_detail'),
]
urlpatterns += router.urls