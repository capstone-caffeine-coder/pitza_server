from django.db import connection
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def profile_setup(request):
    user_id = request.session.get('user')

    if request.method == 'POST':
        nickname = request.POST['nickname']
        birthdate = request.POST['birthdate']
        sex = request.POST['sex']
        blood_type = request.POST['blood_type']
        profile_picture = request.POST.get('profile_picture', '')  # Keep default if empty

        with connection.cursor() as cursor:
            if user_id.startswith("카카오:"):
                kakao_id = user_id.split(":", 1)[1]
                cursor.execute("""
                    UPDATE users SET nickname=%s, birthdate=%s, sex=%s, blood_type=%s, profile_picture=%s
                    WHERE kakao_id=%s
                """, [nickname, birthdate, sex, blood_type, profile_picture, kakao_id])
            else:
                email = user_id
                cursor.execute("""
                    UPDATE users SET nickname=%s, birthdate=%s, sex=%s, blood_type=%s, profile_picture=%s
                    WHERE email=%s
                """, [nickname, birthdate, sex, blood_type, profile_picture, email])

        return redirect('/home/')

    # Preload profile picture for GET request
    with connection.cursor() as cursor:
        if user_id.startswith("카카오:"):
            kakao_id = user_id.split(":", 1)[1]
            cursor.execute("SELECT profile_picture FROM users WHERE kakao_id = %s", [kakao_id])
        else:
            cursor.execute("SELECT profile_picture FROM users WHERE email = %s", [user_id])
        profile_picture = cursor.fetchone()[0]

    return render(request, 'login/profile_setup.html', {'profile_picture': profile_picture})
