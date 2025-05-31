from django.shortcuts import render

import requests
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.conf import settings
from math import radians, cos, sin, asin, sqrt
from .kakao import get_coordinates
from .models import BloodCenter

def haversine(lon1, lat1, lon2, lat2):
    # 두 지점의 위도/ 경도 받아 km 거리 계산
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return 6371 * c

@require_GET
def blood_centers_nearby(request):
    # 클라이언트에서 lat, lon 쿼리 받고 5km 이내 헌혈원 리스트 반환
    lat = request.GET.get("lat")
    lon = request.GET.get("lon")

    if not lat or not lon:
        return JsonResponse({"error": "위도와 경도가 없습니다."}, status=400)

    try:
        user_lat = float(lat)
        user_lon = float(lon)
    except ValueError:
        return JsonResponse({"error": "위도와 경도 float 값으로 작성해야합니다."}, status=400)

    centers = BloodCenter.objects.all()
    filtered_centers = []

    for center in centers:
        distance = haversine(user_lon, user_lat, center.longitude, center.latitude)
        print("distance", distance)
        if distance <= 5:
            filtered_centers.append({
                "id": center.id,
                "name": center.name,
                "address": center.address,
                "phone": center.phone,
                "center_type": center.center_type,
                "blood_office": center.blood_office,
                "latitude": center.latitude,
                "longitude": center.longitude,
                "distance": round(distance,2)
            })
            print("center", center)

    return JsonResponse({"count": len(filtered_centers), "centers": filtered_centers}, json_dumps_params={'ensure_ascii': False})

@require_GET
def blood_centers_all(request):
    centers = BloodCenter.objects.all()

    result = []
    for center in centers:
        result.append({
            "id": center.id,
            "name": center.name,
            "address": center.address,
            "phone": center.phone,
            "center_type": center.center_type,
            "blood_office": center.blood_office,
            "latitude": center.latitude,
            "longitude": center.longitude,
        })

    return JsonResponse({
        "count": len(result),
        "centers": result
    }, json_dumps_params={'ensure_ascii': False})