# login/views/auth_views.py

from django.shortcuts import render, redirect
from urllib.parse import urlencode
import requests
import os
from django.contrib.auth import login
from django.contrib.auth import get_user_model


User = get_user_model()

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI')

KAKAO_CLIENT_ID = os.environ.get('KAKAO_CLIENT_ID')
KAKAO_REDIRECT_URI = os.environ.get('KAKAO_REDIRECT_URI')

def login_view(request):
    return render(request, 'login/login.html')


def login_google(request):
    auth_endpoint = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent"
    }
    return redirect(f"{auth_endpoint}?{urlencode(params)}")


def google_callback(request):
    code = request.GET.get("code")

    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    token_res = requests.post(token_url, data=token_data).json()
    access_token = token_res.get("access_token")

    userinfo_response = requests.get(
        "https://www.googleapis.com/oauth2/v1/userinfo",
        params={"access_token": access_token}
    )
    userinfo = userinfo_response.json()
    email = userinfo.get("email", "")
    google_picture_url = userinfo.get("picture", "")

    user, created = User.objects.get_or_create(email=email)

    if created:
        user.profile_picture_key = google_picture_url
        user.save()

    request.session['user'] = email
    login(request, user)

    if user.nickname:
        return redirect('http://localhost:5173/')
    else:
        return redirect('http://localhost:5173/profile/setup/')


def login_kakao(request):
    return redirect(
        f"https://kauth.kakao.com/oauth/authorize?client_id={KAKAO_CLIENT_ID}&redirect_uri={KAKAO_REDIRECT_URI}&response_type=code"
    )


def kakao_callback(request):
    code = request.GET.get("code")

    token_url = "https://kauth.kakao.com/oauth/token"
    token_data = {
        "grant_type": "authorization_code",
        "client_id": KAKAO_CLIENT_ID,
        "redirect_uri": KAKAO_REDIRECT_URI,
        "code": code
    }

    token_response = requests.post(token_url, data=token_data).json()
    access_token = token_response.get("access_token")

    user_info = requests.get(
        "https://kapi.kakao.com/v2/user/me",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()

    kakao_id = str(user_info["id"])
    profile_image_url = user_info["properties"].get("profile_image")

    user, created = User.objects.get_or_create(kakao_id=kakao_id)

    if created:
        user.profile_picture_key = profile_image_url
        user.save()

    request.session['user'] = f"카카오:{kakao_id}"
    login(request, user)

    if user.nickname:
        return redirect('http://localhost:5173/')
    else:
        return redirect('http://localhost:5173/profile/setup/')