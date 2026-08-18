import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.envelope import error_code_for_status
from app.routers import ai, analysis, auth, basket, foods, health, meals, recipes, recommendations, skin_logs, users

settings = get_settings()

app = FastAPI(title="Skin Basket API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _error_envelope(status_code: int, message: str) -> JSONResponse:
    """API 명세서 v2 공통 에러 포맷: {success:false, data:null, error:{code, message}}."""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "data": None,
            "error": {"code": error_code_for_status(status_code), "message": message},
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return _error_envelope(exc.status_code, str(exc.detail))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return _error_envelope(400, f"요청 형식이 올바르지 않습니다: {exc.errors()}")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # 클라이언트에는 상세 노출 안 함 — 서버 로그에만 스택트레이스 남김.
    logging.exception("Unhandled exception on %s", request.url.path)
    return _error_envelope(500, "서버 내부 오류가 발생했습니다.")


# ai 라우터는 프론트가 이미 하드코딩한 `/ai/food-image` 경로를 위해 prefix 없이 루트에 붙인다
# (응답도 아직 {success,data,error} 봉투 없이 예전 shape 그대로 — routers/ai.py 상단 주석 참고).
# 나머지는 도메인별 prefix로 묶여있고, EnvelopeRoute를 적용해 응답을 {success,data,error}로 감싼다
# (API 명세서 v2 공통 규약). 쇼핑 검색은 백엔드에 없음 — 네이버 쇼핑검색 API가 종료돼서 쿠팡과
# 동일하게 프론트가 검색 결과 페이지로 딥링크만 여는 방식으로 처리한다
# (routers/shopping.py, services/naver_client.py 제거함. 상세: README.md "쇼핑 연동" 항목 참고).
# API 명세가 바뀌면: 여기서 include_router를 추가/삭제하고, 각 routers/*.py 파일 하나만 손보면 됨.
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(meals.router)
app.include_router(foods.router)
app.include_router(analysis.router)
app.include_router(basket.router)
app.include_router(recommendations.router)
app.include_router(recipes.router)
app.include_router(skin_logs.router)
app.include_router(ai.router)
