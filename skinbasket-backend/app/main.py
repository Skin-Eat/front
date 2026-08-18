from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import ai, analysis, basket, health, meals, profiles, recipes, skin_logs

settings = get_settings()

app = FastAPI(title="Skin Basket API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ai 라우터는 프론트가 이미 하드코딩한 `/ai/food-image` 경로를 위해 prefix 없이 루트에 붙인다.
# 나머지는 도메인별 prefix(/auth, /meals, /analysis, /basket, /recipes, /skin-logs)로 묶여있다.
# 쇼핑 검색은 백엔드에 없음 — 네이버 쇼핑검색 API가 종료돼서 쿠팡과 동일하게 프론트가
# 검색 결과 페이지로 딥링크만 여는 방식으로 처리한다 (routers/shopping.py, services/naver_client.py
# 제거함. 상세: README.md "쇼핑 연동" 항목 참고).
# API 명세가 바뀌면: 여기서 include_router를 추가/삭제하고, 각 routers/*.py 파일 하나만 손보면 됨.
app.include_router(health.router)
app.include_router(profiles.router)
app.include_router(meals.router)
app.include_router(analysis.router)
app.include_router(basket.router)
app.include_router(recipes.router)
app.include_router(skin_logs.router)
app.include_router(ai.router)
