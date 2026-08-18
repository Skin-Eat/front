"""규칙 기반(rule-based) 피부 점수/결핍 분석.

Android `SkinScoreCalculator.kt`와 임계값을 반드시 동일하게 유지할 것 — 둘 중 하나만
바뀌면 앱과 서버가 같은 식단에 다른 결과를 낼 수 있음. 값이 바뀌면 프론트 팀에도 알릴 것.

공통 지침 2.1 확정 사항: 점수는 항상 "최근 7일" 단위로만 계산하고 저장하지 않는다.
(단, 프론트는 자체적으로 "오늘 하루치" 점수를 별도로 계산해 홈 화면에 보여주기로 함 —
그건 프론트 책임이고, 이 서비스는 7일 결핍 분석만 제공한다.)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.models.food import Food
from app.models.meal import MealItem, MealLog

HIGH_SUGAR_G = 15.0
HIGH_SAT_FAT_G = 5.0
GOOD_OMEGA3_MG = 500.0
GOOD_VIT_C_MG = 30.0
GOOD_VIT_E_MG = 3.0
GOOD_ZINC_MG = 2.0

RECENT_WINDOW_DAYS = 7

_THRESHOLDS = {"OMEGA3": GOOD_OMEGA3_MG, "VIT_C": GOOD_VIT_C_MG, "VIT_E": GOOD_VIT_E_MG, "ZINC": GOOD_ZINC_MG}


def deficiency_ratio(code: str, average: float | None) -> float | None:
    """평균 섭취량 / 권장량. GET /analysis/diet의 deficiencies[].ratio와
    GET /recommendations/ingredients의 그룹 정렬(부족이 심한 순)이 공유해서 씀."""
    if average is None:
        return None
    return round(average / _THRESHOLDS[code], 4)

# Android SkinScoreCalculator.scoreForItem/scoreForMeals와 동일하게 유지할 것 (값이 바뀌면
# 프론트 팀에도 알릴 것). API 명세서 v2의 GET /analysis/diet의 score.total이 이걸 씀 —
# 지금까지는 결핍 분석(analyze_deficiency)만 포팅돼 있고 점수 자체는 없었음.
BASE_SCORE = 70


@dataclass
class NutrientAverage:
    average: float | None
    sample_count: int


@dataclass
class DeficiencySummary:
    omega3: NutrientAverage
    vit_c: NutrientAverage
    vit_e: NutrientAverage
    zinc: NutrientAverage
    omega3_deficient: bool
    vit_c_deficient: bool
    vit_e_deficient: bool
    zinc_deficient: bool
    high_sugar_meal_count: int
    high_sat_fat_meal_count: int
    deficient_keys: list[str] = field(default_factory=list)


def recent_cutoff(days: int = RECENT_WINDOW_DAYS) -> datetime:
    return datetime.utcnow() - timedelta(days=days)


def _average_nutrient(items: list[MealItem], selector) -> NutrientAverage:
    values = []
    for item in items:
        raw = selector(item.food)
        if raw is not None:
            values.append(raw * item.portion_ratio)
    if not values:
        return NutrientAverage(average=None, sample_count=0)
    return NutrientAverage(average=sum(values) / len(values), sample_count=len(values))


def analyze_deficiency(meal_logs: list[MealLog]) -> DeficiencySummary:
    """meal_logs는 이미 "최근 7일" 범위로 필터링된 상태로 넘어와야 한다 (recent_cutoff 사용)."""
    items: list[MealItem] = [item for log in meal_logs for item in log.items]

    omega3 = _average_nutrient(items, lambda f: f.omega3_mg)
    vit_c = _average_nutrient(items, lambda f: f.vit_c_mg)
    vit_e = _average_nutrient(items, lambda f: f.vit_e_mg)
    zinc = _average_nutrient(items, lambda f: f.zinc_mg)

    def deficient(avg: NutrientAverage, threshold: float) -> bool:
        return avg.average is None or avg.average < threshold

    high_sugar_count = sum(1 for item in items if item.food.sugar_g * item.portion_ratio >= HIGH_SUGAR_G)
    high_sat_fat_count = sum(
        1
        for item in items
        if item.food.sat_fat_g is not None and item.food.sat_fat_g * item.portion_ratio >= HIGH_SAT_FAT_G
    )

    summary = DeficiencySummary(
        omega3=omega3,
        vit_c=vit_c,
        vit_e=vit_e,
        zinc=zinc,
        omega3_deficient=deficient(omega3, GOOD_OMEGA3_MG),
        vit_c_deficient=deficient(vit_c, GOOD_VIT_C_MG),
        vit_e_deficient=deficient(vit_e, GOOD_VIT_E_MG),
        zinc_deficient=deficient(zinc, GOOD_ZINC_MG),
        high_sugar_meal_count=high_sugar_count,
        high_sat_fat_meal_count=high_sat_fat_count,
    )
    if summary.omega3_deficient:
        summary.deficient_keys.append("OMEGA3")
    if summary.vit_c_deficient:
        summary.deficient_keys.append("VIT_C")
    if summary.vit_e_deficient:
        summary.deficient_keys.append("VIT_E")
    if summary.zinc_deficient:
        summary.deficient_keys.append("ZINC")
    return summary


def score_for_item(food: Food, portion_ratio: float) -> int:
    """Android SkinScoreCalculator.scoreForItem 그대로 포팅. NULL 영양소는 결측 취급(가점/감점
    없음) — 값이 있을 때만 채점하는 원칙(공통 지침 2.4)은 analyze_deficiency와 동일."""
    score = BASE_SCORE

    if food.sugar_g * portion_ratio >= HIGH_SUGAR_G:
        score -= 10
    if food.is_high_gi:
        score -= 5
    if food.sat_fat_g is not None and food.sat_fat_g * portion_ratio >= HIGH_SAT_FAT_G:
        score -= 5
    if food.omega3_mg is not None and food.omega3_mg * portion_ratio >= GOOD_OMEGA3_MG:
        score += 10
    if food.vit_c_mg is not None and food.vit_c_mg * portion_ratio >= GOOD_VIT_C_MG:
        score += 5
    if food.vit_e_mg is not None and food.vit_e_mg * portion_ratio >= GOOD_VIT_E_MG:
        score += 5
    if food.zinc_mg is not None and food.zinc_mg * portion_ratio >= GOOD_ZINC_MG:
        score += 5

    return max(0, min(100, score))


def score_for_meals(meal_logs: list[MealLog]) -> int:
    """Android SkinScoreCalculator.scoreForMeals 포팅 — 끼니 없으면 BASE_SCORE, 있으면
    아이템별 점수 평균(반올림)."""
    items = [item for log in meal_logs for item in log.items]
    if not items:
        return BASE_SCORE
    scores = [score_for_item(item.food, item.portion_ratio) for item in items]
    return max(0, min(100, round(sum(scores) / len(scores))))


def logged_days(meal_logs: list[MealLog]) -> int:
    """최근 구간 안에서 실제로 기록이 있었던 날짜 수 — GET /analysis/diet의
    hasEnoughData(loggedDays>=3) 판단에 씀."""
    return len({log.eaten_at.date() for log in meal_logs})
