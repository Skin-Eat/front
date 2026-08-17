"""Supabase Auth가 발급한 JWT를 검증해서 유저 id를 뽑아내는 의존성.

프론트가 로그인/회원가입 자체는 Supabase Auth SDK로 직접 처리하고(백엔드를 거치지 않음),
API를 호출할 때 `Authorization: Bearer <supabase access token>` 헤더로 붙여 보낸다는 전제.
백엔드는 그 토큰을 검증만 하고, profiles 테이블에 앱 전용 데이터(skin_type, concerns 등)를 둔다.

TODO: 실제로 이 전제(프론트가 Supabase Auth를 쓸지)를 프론트/기획 담당자와 확정할 것.
아니라면 이 파일만 바꾸면 되고 라우터 쪽 의존성 시그니처는 그대로 재사용 가능.
"""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import get_settings

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_profile_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> uuid.UUID:
    settings = get_settings()

    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="인증 토큰이 없습니다.")

    if not settings.supabase_jwt_secret:
        if settings.app_env != "local":
            # APP_ENV가 local이 아닌데 시크릿이 없다는 건 배포 설정 실수일 가능성이 높다.
            # 여기서 막지 않으면 UUID만 아는 사람이 아무 프로필이나 사칭할 수 있음.
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SUPABASE_JWT_SECRET이 설정되지 않았습니다 (APP_ENV=local이 아닌 환경에서는 필수).",
            )
        # 로컬 개발 편의용 폴백: .env에 SUPABASE_JWT_SECRET을 아직 안 넣었으면 토큰을
        # 그대로 profile id로 취급한다. 운영/데모 전에는 반드시 실제 검증 경로를 쓸 것.
        try:
            return uuid.UUID(credentials.credentials)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="SUPABASE_JWT_SECRET 미설정 상태에서는 Bearer 값이 profile UUID여야 합니다.",
            ) from exc

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 토큰입니다.") from exc

    subject = payload.get("sub")
    if subject is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="토큰에 사용자 정보가 없습니다.")

    try:
        return uuid.UUID(subject)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="토큰의 sub이 유효한 UUID가 아닙니다.") from exc
