"""Supabase Auth를 서버사이드에서 대신 호출하는 프록시.

API 명세서 v2 결정사항: 프론트는 Supabase를 아예 모르고 우리 API(`/auth/signup`,
`/auth/login`)만 쓴다. 여기서 Supabase Auth REST API(`/auth/v1/signup`,
`/auth/v1/token?grant_type=password`)를 호출해서 얻은 access_token을 그대로 프론트에
돌려준다 — 그 토큰은 기존 `app/core/security.py`가 검증하는 바로 그 Supabase JWT라서,
인증 검증 쪽 코드는 안 바뀐다.

DRAFT: Supabase 프로젝트의 이메일 확인(email confirmation) 설정이 켜져 있으면
/signup이 access_token 없이 미확인 유저만 반환할 수 있음 — 그러면 아래 sign_up()의
session["access_token"] 접근에서 바로 실패한다. 데모 편의를 위해 Supabase 대시보드
Authentication > Providers > Email에서 "Confirm email"을 꺼두는 걸 전제로 짰다.
"""

from __future__ import annotations

import httpx

from app.core.config import get_settings


class SupabaseAuthError(RuntimeError):
    pass


def _headers() -> dict:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise SupabaseAuthError("SUPABASE_URL/SUPABASE_ANON_KEY가 설정되지 않았습니다.")
    return {
        "apikey": settings.supabase_anon_key,
        "Content-Type": "application/json",
    }


async def sign_up(email: str, password: str) -> dict:
    """반환값: {"access_token": ..., "user": {"id": ..., "email": ..., ...}}"""
    settings = get_settings()
    url = f"{settings.supabase_url}/auth/v1/signup"

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, headers=_headers(), json={"email": email, "password": password})

    if response.status_code >= 400:
        raise SupabaseAuthError(f"Supabase 회원가입 실패: {response.status_code} {response.text}")

    data = response.json()
    if not data.get("access_token"):
        # 이메일 확인이 켜져 있으면 여기로 옴 — 위 모듈 docstring의 DRAFT 참고.
        raise SupabaseAuthError(
            "회원가입은 됐지만 access_token이 없습니다 — Supabase 프로젝트의 "
            "이메일 확인(Confirm email) 설정이 켜져 있는지 확인하세요."
        )
    return data


async def sign_in(email: str, password: str) -> dict:
    """반환값: {"access_token": ..., "user": {"id": ..., "email": ..., ...}}"""
    settings = get_settings()
    url = f"{settings.supabase_url}/auth/v1/token"

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            url,
            headers=_headers(),
            params={"grant_type": "password"},
            json={"email": email, "password": password},
        )

    if response.status_code >= 400:
        raise SupabaseAuthError(f"로그인 실패: {response.status_code} {response.text}")

    return response.json()
