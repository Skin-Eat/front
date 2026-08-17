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
