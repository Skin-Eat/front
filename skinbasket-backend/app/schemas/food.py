from app.models.food import FoodSource
from app.schemas.base import CamelModel


class FoodCreate(CamelModel):
    """API 명세서 v2: 없는 메뉴 직접 추가. 세부 영양소(포화지방/오메가3/비타민 등)는 명세서에
    없어서 안 받음 — 결측 취급(NULL, 0 아님)돼서 이 음식은 결핍 분석 평균 계산에서 자동 제외됨.
    """

    name: str
    serving_g: int
    energy_kcal: float
    carb_g: float = 0.0
    sugar_g: float = 0.0
    protein_g: float = 0.0
    fat_g: float = 0.0


class FoodOut(CamelModel):
    id: int
    name: str
    source: FoodSource
    serving_g: int
    energy_kcal: float
    carb_g: float
    sugar_g: float
    protein_g: float
    fat_g: float
    sat_fat_g: float | None
    omega3_mg: float | None
    vit_a_ug: float | None
    vit_c_mg: float | None
    vit_e_mg: float | None
    zinc_mg: float | None
    is_dairy: bool
    is_high_gi: bool
