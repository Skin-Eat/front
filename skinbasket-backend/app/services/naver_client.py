"""네이버 쇼핑 검색 API 프록시. 프론트에서 직접 호출하면 CORS로 막히기 때문에
백엔드 프록시가 필수라는 공통 지침 결정을 그대로 구현한 것.

주의: 네이버 개발자센터에서 애플리케이션 등록 시 반드시 "검색" API를 선택할 것.
"데이터랩 쇼핑인사이트"를 선택하면 403이 남 (공통 지침에 명시된 함정).
"""

from __future__ import annotations

import httpx

from app.core.config import get_settings

NAVER_SHOP_SEARCH_URL = "https://openapi.naver.com/v1/search/shop.json"


class ShoppingSearchError(RuntimeError):
    pass


async def search_products(query: str, display: int = 10) -> dict:
    settings = get_settings()
    if not settings.naver_client_id or not settings.naver_client_secret:
        raise ShoppingSearchError("NAVER_CLIENT_ID / NAVER_CLIENT_SECRET이 설정되지 않았습니다.")

    headers = {
        "X-Naver-Client-Id": settings.naver_client_id,
        "X-Naver-Client-Secret": settings.naver_client_secret,
    }
    params = {"query": query, "display": display, "sort": "sim"}

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(NAVER_SHOP_SEARCH_URL, headers=headers, params=params)

    if response.status_code != 200:
        raise ShoppingSearchError(f"네이버 검색 API 호출 실패: {response.status_code} {response.text}")

    return response.json()
