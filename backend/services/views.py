from math import radians, cos, sin, asin, sqrt
from .models import BloodCenter
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import BloodCenterSerializer
from rest_framework import status
from django.core.mail import send_mail
from rest_framework.views import APIView

def haversine(lon1, lat1, lon2, lat2):
    # 두 지점의 위도/ 경도 받아 km 거리 계산
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return 6371 * c

@swagger_auto_schema(
    method='get',
    manual_parameters=[
        openapi.Parameter('lat', openapi.IN_QUERY, description="위도", type=openapi.TYPE_NUMBER, required=True),
        openapi.Parameter('lon', openapi.IN_QUERY, description="경도", type=openapi.TYPE_NUMBER, required=True),
    ],
    responses={200: BloodCenterSerializer(many=True)}
)
@api_view(['GET'])
def blood_centers_nearby(request):
    # 클라이언트에서 lat, lon 쿼리 받고 5km 이내 헌혈원 리스트 반환
    lat = request.GET.get("lat")
    lon = request.GET.get("lon")

    if not lat or not lon:
        return Response({"error": "위도와 경도가 없습니다."}, status=400)

    try:
        user_lat = float(lat)
        user_lon = float(lon)
    except ValueError:
        return Response({"error": "위도와 경도 float 값으로 작성해야합니다."}, status=400)

    centers = BloodCenter.objects.all()
    filtered_centers = []

    for center in centers:
        distance = haversine(user_lon, user_lat, center.longitude, center.latitude)
        if distance <= 5:
            center.distance = round(distance, 2)
            filtered_centers.append(center)
    serializer = BloodCenterSerializer(filtered_centers, many=True)
    return Response({"count": len(filtered_centers), "centers": serializer.data})

@swagger_auto_schema(
    method='get',
    responses={200: BloodCenterSerializer(many=True)}
)
@api_view(['GET'])
def blood_centers_all(request):
    centers = BloodCenter.objects.all()
    serializer = BloodCenterSerializer(centers, many=True)
    return Response({"count": len(centers), "centers": serializer.data})


class SendMatchSuccessEmailView(APIView):

    @swagger_auto_schema(
        responses={
            200: openapi.Response(description="이메일 전송 완료"),
            400: openapi.Response(description="이메일 주소가 필요합니다."),
        }
    )
    def post(self, request):
        to_email = request.user.email
        # to_email = 'pitza2025@gmail.com'
        donor_name = getattr(request.user, 'nickname', '사용자')

        if not to_email:
            return Response({'error': '이메일 주소가 필요합니다.'}, status=status.HTTP_400_BAD_REQUEST)

        subject = "[핏자] 지정헌혈 매칭이 완료되었습니다!"
        message = f"""
        안녕하세요, 핏자입니다!

        {donor_name} 님과의 지정헌혈 매칭이 완료되었습니다.
        헌혈을 진행해 주세요.

        감사합니다.
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=None,
            recipient_list=[to_email],
            fail_silently=False
        )

        return Response({'message': '이메일 전송 완료'}, status=status.HTTP_200_OK)
