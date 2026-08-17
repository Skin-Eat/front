from fastapi import APIRouter, HTTPException

from app.services.naver_client import ShoppingSearchError, search_products

router = APIRouter(prefix="/shopping", tags=["shopping"])


@router.get("/search")
async def search(query: str, display: int = 10):
    """네이버 검색 API 프록시. 쿠팡/컬리는 상품 데이터가 없으므로(공통 지침 2.3) 여기서
    다루지 않고, 프론트가 검색 딥링크 버튼으로 직접 연결한다."""
    try:
        return await search_products(query=query, display=display)
    except ShoppingSearchError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
