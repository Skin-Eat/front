import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.envelope import EnvelopeRoute
from app.db.session import get_db
from app.models.profile import Profile
from app.schemas.auth import AuthResponse, LoginRequest, SignupRequest, UserOut
from app.services.supabase_auth import SupabaseAuthError, sign_in, sign_up

router = APIRouter(prefix="/auth", tags=["auth"], route_class=EnvelopeRoute)


@router.post("/signup", response_model=AuthResponse)
async def signup(body: SignupRequest, db: Session = Depends(get_db)):
    """API 명세서 v2: 프론트는 Supabase를 모르고 이 API만 씀. 우리가 Supabase Auth를
    대신 호출해서 얻은 access_token을 그대로 돌려준다 (services/supabase_auth.py 참고).

    DRAFT: skinType/concerns를 온보딩 화면에서 나중에 입력받는 프론트 플로우와
    가입 시점 필수값 요구가 충돌한다는 걸 프론트 문서에서도 지적함 — 지금은 명세서
    그대로 "가입 시 필수"로 구현했고, 순서를 바꾸고 싶으면(기본값 가입 -> 온보딩 후
    PATCH /users/me) 프론트에서 기본값을 채워 보내면 되고 이 엔드포인트는 안 바뀌어도 됨.
    """
    try:
        session = await sign_up(body.email, body.password)
    except SupabaseAuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    profile_id = uuid.UUID(session["user"]["id"])
    profile = db.get(Profile, profile_id)
    if profile is None:
        profile = Profile(
            id=profile_id,
            nickname=body.nickname,
            skin_type=body.skin_type,
            concerns=body.concerns,
            photo_consent=body.photo_consent,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

    return AuthResponse(access_token=session["access_token"], user=UserOut.model_validate(profile))


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, db: Session = Depends(get_db)):
    try:
        session = await sign_in(body.email, body.password)
    except SupabaseAuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    profile_id = uuid.UUID(session["user"]["id"])
    profile = db.get(Profile, profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="프로필이 없습니다. 회원가입을 먼저 완료하세요.")

    return AuthResponse(access_token=session["access_token"], user=UserOut.model_validate(profile))
