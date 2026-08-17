"""Gemini 연동. 공통 지침이 정한 AI 3역할을 여기서 다 다룬다:
  ① 사진 -> 음식 인식 (구현 완료, recognize_food)
  ② 결핍 분석 -> 자연어 코멘트 생성 (DRAFT, generate_analysis_comment)
  ③ 부족 영양소 기반 즉석 레시피 생성 (DRAFT, generate_recipe_suggestion)

①만 프론트(Android)가 이미 호출하는 확정 계약이고, ②③은 API 명세/DB가 아직 안 굳어서
"틀"만 잡아둔 상태 — 함수 시그니처와 프롬프트 구조는 있지만 응답 shape, 저장 여부,
실패 시 폴백 정책은 팀 논의 후 조정 필요 (각 함수 docstring의 DRAFT 항목 참고).

키가 없거나 호출이 실패하면 예외를 던진다 — 프론트는 이미 실패 시 "다시 시도" UI가
있으므로(FoodLogScreen의 AiFoodErrorCard), 여기서 억지로 빈 성공 응답을 만들 필요 없음.
②③도 일단 같은 원칙(실패 -> 예외 -> 라우터에서 502)으로 맞춰뒀다.
"""

from __future__ import annotations

import base64
import json
import re

import httpx

from app.core.config import get_settings
from app.services.skin_score import DeficiencySummary

GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

NUTRIENT_LABELS = {
    "OMEGA3": "오메가3",
    "VIT_C": "비타민C",
    "VIT_E": "비타민E",
    "ZINC": "아연",
}


class GeminiError(RuntimeError):
    """세 기능 공통 베이스. 구분 없이 다 잡고 싶으면 이걸로, 기능별로 다르게 처리하고
    싶으면 아래 서브클래스로 잡으면 됨."""


class FoodRecognitionError(GeminiError):
    pass


class AnalysisCommentError(GeminiError):
    pass


class RecipeGenerationError(GeminiError):
    pass


async def _call_gemini(parts: list[dict], error_cls: type[GeminiError]) -> str:
    """세 기능이 공유하는 Gemini 호출 뼈대. 텍스트 응답 하나(parts[0].text)만 뽑아 돌려준다."""
    settings = get_settings()
    if not settings.gemini_api_key:
        raise error_cls("GEMINI_API_KEY가 설정되지 않았습니다.")

    payload = {"contents": [{"parts": parts}]}

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            GEMINI_ENDPOINT,
            params={"key": settings.gemini_api_key},
            json=payload,
        )

    if response.status_code != 200:
        raise error_cls(f"Gemini 호출 실패: {response.status_code} {response.text}")

    data = response.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as exc:
        raise error_cls("Gemini 응답 형식이 예상과 다릅니다.") from exc


# ── ① 사진 -> 음식 인식 (구현 완료) ─────────────────────────────────────────


def _build_food_prompt(candidates: list[str]) -> str:
    candidate_list = ", ".join(candidates)
    return (
        "다음은 사용자가 촬영한 음식 사진입니다. 아래 후보 목록에 있는 음식 이름 중에서만 골라, "
        "사진과 가장 비슷한 순서로 최대 3개를 고르세요.\n"
        f"후보 목록: [{candidate_list}]\n"
        "반드시 후보 목록에 있는 문자열 그대로, JSON 배열 하나만 출력하세요. "
        '예: ["마라탕", "짬뽕"]  다른 설명은 출력하지 마세요.'
    )


def _extract_json_array(text: str) -> list[str]:
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        return []
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []
    return [item for item in parsed if isinstance(item, str)]


async def recognize_food(image_bytes: bytes, candidates: list[str]) -> list[str]:
    """공통 지침의 "절대 규칙 2"를 지키기 위해 자유 인식이 아니라 항상 candidates
    (=food 테이블에서 뽑은 후보 목록)만 고르게 프롬프트로 강제한다."""
    parts = [
        {"text": _build_food_prompt(candidates)},
        {
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(image_bytes).decode("ascii"),
            }
        },
    ]
    text = await _call_gemini(parts, FoodRecognitionError)

    picked = _extract_json_array(text)
    candidate_set = set(candidates)
    return [name for name in picked if name in candidate_set]


# ── ② 결핍 분석 -> 자연어 코멘트 (DRAFT) ────────────────────────────────────


def _build_analysis_comment_prompt(summary: DeficiencySummary) -> str:
    deficient_labels = [NUTRIENT_LABELS[key] for key in summary.deficient_keys if key in NUTRIENT_LABELS]
    deficient_text = ", ".join(deficient_labels) if deficient_labels else "특별히 부족한 영양소 없음"
    return (
        "당신은 사용자의 최근 7일 식단 기록을 담백하게 요약해주는 도우미입니다. "
        "아래 데이터를 바탕으로 2~3문장의 한국어 코멘트를 작성하세요.\n\n"
        f"- 부족한 영양소: {deficient_text}\n"
        f"- 당류 과다 섭취 끼니 수: {summary.high_sugar_meal_count}\n"
        f"- 포화지방 과다 섭취 끼니 수: {summary.high_sat_fat_meal_count}\n\n"
        "규칙:\n"
        "1. '~때문에 피부가 나빠진다'처럼 인과를 단정하는 표현은 절대 쓰지 말 것 "
        "(recipe.skin_benefits와 동일한 observed_pattern 톤 — '~와 함께 나타나는 경향이 있어요' 식으로).\n"
        "2. 진단/의학적 조언처럼 들리는 표현 금지.\n"
        "3. 다른 설명 없이 코멘트 문장만 출력."
    )


async def generate_analysis_comment(summary: DeficiencySummary) -> str:
    """AI 역할 ②의 틀.

    DRAFT — 아직 안 정한 것들:
    - 코멘트를 1개만 줄지, 영양소별로 나눠서 줄지
    - 실패 시 502로 보낼지, 규칙 기반 기본 문구로 폴백할지
    (지금은 recognize_food와 동일하게 "실패하면 예외" 방식으로 맞춰뒀다.)
    """
    text = await _call_gemini([{"text": _build_analysis_comment_prompt(summary)}], AnalysisCommentError)
    return text.strip()


# ── ③ 부족 영양소 기반 즉석 레시피 생성 (DRAFT) ─────────────────────────────


def _build_recipe_prompt(
    deficient_keys: list[str],
    allergy_ingredients: list[str],
    dislike_ingredients: list[str],
) -> str:
    deficient_labels = [NUTRIENT_LABELS[key] for key in deficient_keys if key in NUTRIENT_LABELS]
    deficient_text = ", ".join(deficient_labels) if deficient_labels else "특별히 없음 (균형 잡힌 레시피면 충분)"
    allergy_text = ", ".join(allergy_ingredients) if allergy_ingredients else "없음"
    dislike_text = ", ".join(dislike_ingredients) if dislike_ingredients else "없음"
    return (
        "다음 조건에 맞는 한국 가정식 레시피를 하나 만들어 주세요.\n"
        f"- 보충하고 싶은 영양소: {deficient_text}\n"
        f"- 반드시 제외할 재료(알레르기): {allergy_text}\n"
        f"- 가능하면 피할 재료(비선호, 대체재로 바꿔도 됨): {dislike_text}\n\n"
        "다음 JSON 스키마 그대로, 다른 설명 없이 JSON 객체 하나만 출력하세요:\n"
        "{\n"
        '  "name": "레시피 이름",\n'
        '  "cooking_time_minutes": 15,\n'
        '  "servings": "1인분",\n'
        '  "ingredients": ["재료1", "재료2"],\n'
        '  "steps": ["1단계 설명", "2단계 설명"],\n'
        '  "skin_benefits": [{"nutrient": "오메가3", "description": "..."}]\n'
        "}\n\n"
        "skin_benefits의 description은 '~때문에/때문이다' 같은 인과 단정 표현 대신 "
        "관찰 패턴 톤('~와 함께 나타나는 경향' 등)으로 작성하세요."
    )


def _extract_json_object(text: str) -> dict | None:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


async def generate_recipe_suggestion(
    deficient_keys: list[str],
    allergy_ingredients: list[str],
    dislike_ingredients: list[str],
) -> dict:
    """AI 역할 ③의 틀. DB에 미리 넣어둔 recipe 테이블과 달리, 매 호출마다 즉석으로 생성한다.

    DRAFT — 아직 안 정한 것들 (팀 논의 필요):
    - 여기서 만든 레시피를 recipe 테이블에 저장해서 재사용할지, 매번 휘발성으로만 쓸지
    - ingredients 문자열이 food 테이블 이름과 안 맞으면 POST /recipes/{id}/eat 같은
      "먹었어요" 폐쇄 루프에 못 들어감 (routers/recipes.py의 이름 매칭과 같은 한계)
    - 응답 shape를 RecipeOut과 완전히 맞출지(지금은 id가 없다는 차이만 있음)
    지금은 함수 시그니처/프롬프트 구조만 잡아둔 상태 — 실제로 Gemini가 스키마를
    깨는 응답을 줄 수 있으므로 호출부(routers/ai.py)에서 pydantic 검증 실패를 502로 처리한다.
    """
    prompt = _build_recipe_prompt(deficient_keys, allergy_ingredients, dislike_ingredients)
    text = await _call_gemini([{"text": prompt}], RecipeGenerationError)

    parsed = _extract_json_object(text)
    if parsed is None:
        raise RecipeGenerationError("Gemini 응답에서 JSON 객체를 추출하지 못했습니다.")
    return parsed
