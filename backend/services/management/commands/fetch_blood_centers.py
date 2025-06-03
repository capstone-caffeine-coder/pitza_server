from django.core.management.base import BaseCommand
from django.conf import settings
from services.models import BloodCenter
from services.kakao import get_coordinates
import requests

class Command(BaseCommand):
    help = "Fetch blood centers from API and store to DB only if DB is empty"

    def handle(self, *args, **kwargs):
        if BloodCenter.objects.exists():
            self.stdout.write(self.style.WARNING("이미 데이터가 존재합니다. 작업을 중단합니다."))
            return

        url = "https://api.odcloud.kr/api/15050729/v1/uddi:4879af1f-c19f-40ee-b8b8-cfb415a04645"
        params = {
            "page": 1,
            "perPage": 200,
            "serviceKey": settings.OPENAPI_SERVICE_KEY,
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            self.stderr.write(f"API 호출 실패: {e}")
            return

        for center in data.get("data", []):
            address = center.get("주소지")
            if not address:
                continue
            lat, lon = get_coordinates(address, settings.KAKAO_REST_API_KEY)
            if lat is None or lon is None:
                continue

            BloodCenter.objects.create(
                name=center.get("헌혈의 집", ""),
                address=address,
                phone=center.get("전화번호", ""),
                center_type=center.get("구분", ""),
                blood_office=center.get("혈액원", ""),
                latitude=lat,
                longitude=lon,
            )
        self.stdout.write(self.style.SUCCESS("헌혈의 집 데이터를 DB에 저장 완료"))