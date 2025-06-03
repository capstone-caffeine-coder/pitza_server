import requests

def get_coordinates(address: str, kakao_api_key: str):
    
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {kakao_api_key}"}
    params = {"query": address}

    try:
        res = requests.get(url, headers=headers, params=params)
        res.raise_for_status()
        data = res.json()

        if data["documents"]:
            location = data["documents"][0]["address"]
            lat = float(location["y"])
            lon = float(location["x"])
            return lat, lon
    except Exception:
        pass

    return None, None  # 좌표 변환 실패 시