import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_profile_id
from app.db.session import get_db
from app.models.food import Food
from app.models.profile import ConstraintType, Profile
from app.schemas.ai import AIRecipeSuggestionOut, AnalysisCommentResponse, FoodImageAnalysisResponse
from app.services.openai_client import (
    AnalysisCommentError,
    FoodRecognitionError,
    RecipeGenerationError,
    generate_analysis_comment,
    generate_recipe_suggestion,
    recognize_food,
)
from app.services.meal_query import get_recent_meal_logs
from app.services.skin_score import analyze_deficiency

# 주의: 이 라우터는 의도적으로 prefix가 없다. Android SkinBasketApi.kt가
# `@POST("ai/food-image")`로 이미 하드고딩돼 있어서(프론트 폴더는 건드리지 않기로 함),
# 경로를 `/ai/food-image`로 정확히 맞춰야 함. 다른 라우터들처럼 prefix를 붙이고 싶으면
# 반드시 프론트 팀과 먼저 맞출 것.
#
# 그래서 이 라우터에는 다른 라우터들과 달리 route_class=EnvelopeRoute를 아직 안 붙였다 —
# 붙이면 응답이 {candidates:[...]}에서 {success,data:{candidates:[...]},error:null}로
# 바뀌어서 안드로이드가 이미 하드코딩한 FoodImageAnalysisResponse 파싱이 깨진다.
# API 명세서 v2는 이 엔드포인트를 POST /meals/analyze-photo로 옮기는 걸 전제로 하는데,
# 그 마이그레이션(경로+응답 shape+프론트 코드) 하기 전까지는 지금 계약을 그대로 유지한다.
router = APIRouter(prefix="/ai", tags=["ai"])

MAX_CANDIDATES = 50


@router.post("/food-image", response_model=FoodImageAnalysisResponse)
async def analyze_food_image(image: UploadFile, db: Session = Depends(get_db)):
    """AI 역할 ①: 사진 -> 음식 인식. 절대 규칙: 자유 인식이 아니라 food 테이블
    후보 목록(최대 50종) 중에서만 고르게 한다."""
    candidate_names = db.scalars(select(Food.name).limit(MAX_CANDIDATES)).all()
    if not candidate_names:
        raise HTTPException(status_code=500, detail="food 테이블이 비어있어 후보를 만들 수 없습니다.")

    image_bytes = await image.read()

    try:
        candidates = await recognize_food(image_bytes, list(candidate_names))
    except FoodRecognitionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return FoodImageAnalysisResponse(candidates=candidates)


# ── 아래 두 엔드포인트는 DRAFT (틀만 잡아둔 상태) ────────────────────────────
# API 명세/DB가 아직 안 굳어서 경로/응답 shape가 바뀔 수 있음. 프론트가 실제로 쓰기 전에
# 팀과 맞출 것. 로직 자체는 동작한다(OPENAI_API_KEY만 있으면 바로 호출 가능).


@router.post("/analysis-comment", response_model=AnalysisCommentResponse)
async def get_analysis_comment(
    profile_id: uuid.UUID = Depends(get_current_profile_id),
    db: Session = Depends(get_db),
):
    """AI 역할 ②의 틀: /analysis/deficiency와 같은 데이터를 자연어 코멘트로 바꿔준다.
    DRAFT — 별도 엔드포인트로 둘지, /analysis/deficiency 응답에 필드로 얹을지는 미확정."""
    summary = analyze_deficiency(get_recent_meal_logs(db, profile_id))
    try:
        comment = await generate_analysis_comment(summary)
    except AnalysisCommentError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return AnalysisCommentResponse(comment=comment)


@router.post("/recipe-suggestion", response_model=AIRecipeSuggestionOut)
async def get_recipe_suggestion(
    profile_id: uuid.UUID = Depends(get_current_profile_id),
    db: Session = Depends(get_db),
):
    """AI 역할 ③의 틀: recipe 테이블의 고정 레시피 대신, 프로필의 부족 영양소/제약을
    반영해 즉석 레시피를 생성한다. DRAFT — 저장 여부/food 테이블 매칭은
    services/openai_client.py의 generate_recipe_suggestion docstring 참고."""
    profile = db.get(Profile, profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="프로필이 없습니다. 온보딩을 먼저 완료하세요.")

    summary = analyze_deficiency(get_recent_meal_logs(db, profile_id))
    allergies = [c.ingredient_name for c in profile.constraints if c.type == ConstraintType.ALLERGY]
    dislikes = [c.ingredient_name for c in profile.constraints if c.type == ConstraintType.DISLIKE]

    try:
        recipe = await generate_recipe_suggestion(summary.deficient_keys, allergies, dislikes)
    except RecipeGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    try:
        return AIRecipeSuggestionOut(**recipe)
    except ValidationError as exc:
        raise HTTPException(status_code=502, detail="OpenAI가 예상한 형식으로 응답하지 않았습니다.") from exc
