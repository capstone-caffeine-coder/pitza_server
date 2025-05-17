from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from login.models import User

@csrf_exempt
def profile_setup(request):
    user_id = request.session.get('user')

    if request.method == 'POST':
        nickname = request.POST['nickname']
        birthdate = request.POST['birthdate']
        sex = request.POST['sex']
        blood_type = request.POST['blood_type']
        profile_picture = request.POST.get('profile_picture', '')

        if user_id.startswith("카카오:"):
            kakao_id = user_id.split(":", 1)[1]
            user = User.objects.filter(kakao_id=kakao_id).first()
        else:
            user = User.objects.filter(email=user_id).first()

        if user:
            user.nickname = nickname
            user.birthdate = birthdate
            user.sex = sex
            user.blood_type = blood_type
            user.profile_picture = profile_picture
            user.save()

        return redirect('http://localhost:5173/')

    # GET: Load profile picture
    if user_id.startswith("카카오:"):
        kakao_id = user_id.split(":", 1)[1]
        user = User.objects.filter(kakao_id=kakao_id).first()
    else:
        user = User.objects.filter(email=user_id).first()

    profile_picture = user.profile_picture if user else ""


    return redirect('http://localhost:5173/')