from app.schemas.base import CamelModel


class NutrientAxisOut(CamelModel):
    """4축(OMEGA3/VIT_C/VIT_E/ZINC) 중 하나. 명세서는 axes 내부 shape을 구체적으로
    정하지 않아서(그냥 "4개 축"), 이미 있는 실제 데이터(평균/결핍 여부)를 그대로 노출하는
    쪽으로 정함 — 임의의 점수 분배를 지어내지 않기 위함."""

    code: str
    average: float | None
    is_deficient: bool


class ScoreOut(CamelModel):
    total: int
    axes: list[NutrientAxisOut]


class DeficiencyItemOut(CamelModel):
    code: str
    ratio: float | None
    priority: int


class DietAnalysisOut(CamelModel):
    has_enough_data: bool
    score: ScoreOut
    deficiencies: list[DeficiencyItemOut]
    summary: str
    window_days: int
