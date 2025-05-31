from django.shortcuts import render

import requests
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.conf import settings
from math import radians, cos, sin, asin, sqrt
from .kakao import get_coordinates

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
    # 클라이언트에서 lat, lon 쿼리 받고 헌혈원 API 조회 후 5km 이내 헌혈원 리스트 반환
    lat = request.GET.get("lat")
    lon = request.GET.get("lon")

    if not lat or not lon:
        return JsonResponse({"error": "위도와 경도가 없습니다."}, status=400)

    try:
        user_lat = float(lat)
        user_lon = float(lon)
    except ValueError:
        return JsonResponse({"error": "위도와 경도 float 값으로 작성해야합니다."}, status=400)

    # 대한적십자사 헌혈의 집 오픈 API
    openapi_url = "https://api.odcloud.kr/api/15050729/v1/uddi:4879af1f-c19f-40ee-b8b8-cfb415a04645"
    params = {
        "page": 1,
        "perPage": 200,
        "serviceKey": settings.OPENAPI_SERVICE_KEY,
    }

    try:
        response = requests.get(openapi_url, params=params)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        return JsonResponse({"error": "공공 API 데이터를 불러오지 못했습니다.", "details": str(e)}, status=500)

    centers = data.get("data", [])
    filtered_centers = []

    for center in centers:
        address = center.get("주소지")
        if not address:
            continue

        center_lat, center_lon = get_coordinates(address, settings.KAKAO_REST_API_KEY)
        if center_lat is None or center_lon is None:
            continue

        distance = haversine(user_lon, user_lat, center_lon, center_lat)
        if distance <= 5:
            center["distance_km"] = round(distance, 2)
            center["latitude"] = center_lat
            center["longitude"] = center_lon
            filtered_centers.append(center)

    return JsonResponse({"count": len(filtered_centers), "centers": filtered_centers}, json_dumps_params={'ensure_ascii': False})


@require_GET
def blood_centers_all(request):
    # 전체 헌혈의 집 데이터를 좌표 포함해서 반환
    openapi_url = "https://api.odcloud.kr/api/15050729/v1/uddi:4879af1f-c19f-40ee-b8b8-cfb415a04645"
    params = {
        "page": 1,
        "perPage": 200,
        "serviceKey": settings.OPENAPI_SERVICE_KEY,
    }

    try:
        response = requests.get(openapi_url, params=params)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        return JsonResponse({"error": "공공 API 데이터를 불러오지 못했습니다.", "details": str(e)}, status=500)

    centers = data.get("data", [])
    enriched_centers = []

    for center in centers:
        address = center.get("주소지")
        if not address:
            continue

        center_lat, center_lon = get_coordinates(address, settings.KAKAO_REST_API_KEY)
        if center_lat is None or center_lon is None:
            continue

        center["latitude"] = center_lat
        center["longitude"] = center_lon
        enriched_centers.append(center)

    return JsonResponse({"count": len(enriched_centers), "centers": enriched_centers}, json_dumps_params={'ensure_ascii': False})

