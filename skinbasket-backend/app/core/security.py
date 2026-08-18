"""Supabase Auth가 발급한 JWT를 검증해서 유저 id를 뽑아내는 의존성.

프론트는 우리 `/auth/signup`, `/auth/login`(app/services/supabase_auth.py가 Supabase를
대신 호출)에서 받은 accessToken을 그대로 `Authorization: Bearer` 헤더에 넣어 보낸다.
그 토큰은 Supabase가 서명한 진짜 JWT라서, 여기서는 검증만 한다.

실제로 붙여보고 알게 된 것: 이 Supabase 프로젝트는 레거시 HS256(공유 시크릿) 방식이
아니라 **비대칭키(ES256) 방식**으로 토큰을 발급한다(대시보드에 "Legacy JWT Secret"이
보여도, 실제 발급은 새 서명키 시스템을 쓰면 ES256이 나옴). 그래서 토큰 헤더의 alg를 보고
분기한다 — HS256이면 SUPABASE_JWT_SECRET으로, 그 외(ES256 등)면 Supabase의 JWKS
(`/auth/v1/.well-known/jwks.json`)에서 공개키를 받아 검증한다.
"""

import uuid

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import get_settings

bearer_scheme = HTTPBearer(auto_error=False)

# 프로세스 생존 기간 동안 재사용 — Supabase가 서명키를 로테이션하면 kid를 못 찾을 때
# 한 번 더 받아오는 것으로 대응한다(아래 _find_jwk 호출부 참고).
_jwks_cache: dict | None = None


def _fetch_jwks(supabase_url: str, *, force_refresh: bool = False) -> dict:
    global _jwks_cache
    if _jwks_cache is None or force_refresh:
        response = httpx.get(f"{supabase_url}/auth/v1/.well-known/jwks.json", timeout=10.0)
        response.raise_for_status()
        _jwks_cache = response.json()
    return _jwks_cache


def _find_jwk(supabase_url: str, kid: str | None) -> dict | None:
    jwks = _fetch_jwks(supabase_url)
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
    # 캐시가 오래돼서(키 로테이션 등) 못 찾았을 수 있으니 한 번만 강제로 다시 받아본다.
    jwks = _fetch_jwks(supabase_url, force_refresh=True)
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
    return None


def get_current_profile_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> uuid.UUID:
    settings = get_settings()

    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="인증 토큰이 없습니다.")

    if not settings.supabase_jwt_secret and not settings.supabase_url:
        if settings.app_env != "local":
            # APP_ENV가 local이 아닌데 검증 수단이 하나도 없다는 건 배포 설정 실수일 가능성이 높다.
            # 여기서 막지 않으면 UUID만 아는 사람이 아무 프로필이나 사칭할 수 있음.
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SUPABASE_JWT_SECRET/SUPABASE_URL이 둘 다 없습니다 (APP_ENV=local이 아닌 환경에서는 필수).",
            )
        # 로컬 개발 편의용 폴백: .env에 아무것도 안 넣었으면 토큰을 그대로 profile id로 취급한다.
        # 운영/데모 전에는 반드시 실제 검증 경로를 쓸 것.
        try:
            return uuid.UUID(credentials.credentials)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="SUPABASE_JWT_SECRET 미설정 상태에서는 Bearer 값이 profile UUID여야 합니다.",
            ) from exc

    try:
        header = jwt.get_unverified_header(credentials.credentials)
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="토큰 형식이 올바르지 않습니다.") from exc

    alg = header.get("alg", "HS256")

    try:
        if alg == "HS256":
            if not settings.supabase_jwt_secret:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="HS256 토큰 검증용 시크릿이 없습니다.")
            key: str | dict = settings.supabase_jwt_secret
        else:
            key = _find_jwk(settings.supabase_url, header.get("kid"))
            if key is None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="토큰 서명 키를 찾을 수 없습니다.")

        payload = jwt.decode(credentials.credentials, key, algorithms=[alg], audience="authenticated")
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 토큰입니다.") from exc

    subject = payload.get("sub")
    if subject is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="토큰에 사용자 정보가 없습니다.")

    try:
        return uuid.UUID(subject)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="토큰의 sub이 유효한 UUID가 아닙니다.") from exc
