from django.contrib import admin
from django.urls import path
from login import views
from login.views.auth_views import login_view, login_google, google_callback, login_kakao, kakao_callback
from login.views.user_views import user_detail  # Import your user detail view

urlpatterns = [
    path('admin/', admin.site.urls),

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