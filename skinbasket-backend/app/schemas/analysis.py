from pydantic import BaseModel


class NutrientAverageOut(BaseModel):
    average: float | None
    sample_count: int


class DeficiencyOut(BaseModel):
    omega3: NutrientAverageOut
    vit_c: NutrientAverageOut
    vit_e: NutrientAverageOut
    zinc: NutrientAverageOut
    deficient_keys: list[str]
    high_sugar_meal_count: int
    high_sat_fat_meal_count: int
    window_days: int
