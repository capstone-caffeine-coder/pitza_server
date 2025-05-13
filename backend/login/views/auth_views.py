from django.shortcuts import render

# login/views.py

from django.shortcuts import render, redirect
from django.db import connection
from urllib.parse import urlencode
import requests
from login.models import User



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
    picture = userinfo.get("picture", "")

    user, created = User.objects.get_or_create(email=email, defaults={"profile_picture": picture})
    request.session['user'] = email

    if user.nickname:
        return redirect('/home/')
    else:
        return redirect('/profile/setup/')



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
    nickname = user_info["properties"].get("nickname")
    profile_image = user_info["properties"].get("profile_image")

    user, created = User.objects.get_or_create(
        kakao_id=kakao_id,
        defaults={"profile_picture": profile_image}
    )
    request.session['user'] = f"카카오:{kakao_id}"

    if nickname:
        return redirect('/home/')
    else:
        return redirect('/profile/setup/')