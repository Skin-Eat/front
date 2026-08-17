from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import ai, analysis, basket, health, meals, profiles, recipes, shopping, skin_logs

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
# 나머지는 도메인별 prefix(/auth, /meals, /analysis, /basket, /recipes, /skin-logs, /shopping)로 묶여있다.
# API 명세가 바뀌면: 여기서 include_router를 추가/삭제하고, 각 routers/*.py 파일 하나만 손보면 됨.
app.include_router(health.router)
app.include_router(profiles.router)
app.include_router(meals.router)
app.include_router(analysis.router)
app.include_router(basket.router)
app.include_router(recipes.router)
app.include_router(skin_logs.router)
app.include_router(shopping.router)
app.include_router(ai.router)
