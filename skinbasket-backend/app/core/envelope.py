"""API 명세서 v2의 공통 응답 봉투: 성공은 {success:true, data:.., error:null},
실패는 {success:false, data:null, error:{code, message}}.

라우터 함수들은 지금처럼 그냥 Pydantic 모델/리스트를 리턴하면 된다 — EnvelopeRoute가
직렬화 시점에 data로 감싸준다. 에러는 main.py의 예외 핸들러가 처리(라우터에서
HTTPException을 그대로 던지면 됨, 지금 코드 안 바꿔도 됨).
"""

from __future__ import annotations

import json
from collections.abc import Callable

from fastapi import Request, Response
from fastapi.routing import APIRoute

# 명세서 0번 항목의 에러 코드 매핑
STATUS_TO_ERROR_CODE = {
    400: "VALIDATION_ERROR",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    422: "VALIDATION_ERROR",
}


def error_code_for_status(status_code: int) -> str:
    return STATUS_TO_ERROR_CODE.get(status_code, "INTERNAL_ERROR")


class EnvelopeRoute(APIRoute):
    """2xx JSON 응답만 {success:true, data:<원래 응답>, error:null}로 감싼다.
    라우터가 직접 던지는 HTTPException은 여기를 안 거치고 main.py의 예외 핸들러로 감(그쪽에서
    에러 봉투를 만듦) — 이 클래스는 "정상적으로 끝난" 응답만 다룬다."""

    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def envelope_route_handler(request: Request) -> Response:
            response = await original_route_handler(request)
            if 200 <= response.status_code < 300 and response.media_type == "application/json":
                original = json.loads(response.body) if response.body else None
                wrapped = {"success": True, "data": original, "error": None}
                body = json.dumps(wrapped, ensure_ascii=False).encode("utf-8")
                response.body = body
                response.headers["content-length"] = str(len(body))
            return response

        return envelope_route_handler
