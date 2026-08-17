"""최소 시드 데이터. Android 프론트의 FoodSeedData.kt / IngredientSeedData.kt와
값을 맞춰뒀음 — 프론트가 이름으로 찾는 음식(라면, 치킨, 연어 등)이 실제로 존재해야
데모 시나리오가 앞뒤로 맞는다. DB 스키마가 확정되면 이 파일이 가장 먼저 깨질 파일이니
그때 여기부터 고칠 것.

실행: (.venv 활성화 후) python scripts/seed.py
"""

from app.db.session import SessionLocal
from app.models.food import Food, FoodSource
from app.models.ingredient import Ingredient, PriceBand

FOODS = [
    # name, energy, carb, sugar, protein, fat, sat_fat, omega3, vit_a, vit_c, vit_e, zinc, is_dairy, is_high_gi
    Food(name="라면", source=FoodSource.MFDS, serving_g=120, energy_kcal=500, carb_g=78, sugar_g=5, protein_g=10, fat_g=16, sat_fat_g=8, is_high_gi=True),
    Food(name="치킨", source=FoodSource.MFDS, serving_g=300, energy_kcal=800, carb_g=30, sugar_g=3, protein_g=45, fat_g=55, sat_fat_g=12),
    Food(name="마라탕", source=FoodSource.MFDS, serving_g=500, energy_kcal=650, carb_g=40, sugar_g=8, protein_g=25, fat_g=40, sat_fat_g=15),
    Food(name="그릭 요거트와 블루베리", source=FoodSource.MFDS, serving_g=200, energy_kcal=180, carb_g=20, sugar_g=12, protein_g=15, fat_g=3, vit_c_mg=10, is_dairy=True),
    Food(name="햄버거", source=FoodSource.MFDS, serving_g=250, energy_kcal=550, carb_g=45, sugar_g=9, protein_g=25, fat_g=30, sat_fat_g=11, is_high_gi=True),
    Food(name="피자", source=FoodSource.MFDS, serving_g=300, energy_kcal=750, carb_g=80, sugar_g=8, protein_g=30, fat_g=32, sat_fat_g=14, is_dairy=True),
    Food(name="샐러드", source=FoodSource.MFDS, serving_g=200, energy_kcal=150, carb_g=15, sugar_g=4, protein_g=6, fat_g=8, vit_c_mg=35, vit_e_mg=4),
    Food(name="연어", source=FoodSource.MFDS, serving_g=150, energy_kcal=280, carb_g=0, sugar_g=0, protein_g=30, fat_g=18, omega3_mg=1800, vit_e_mg=3.5),
    Food(name="떡볶이", source=FoodSource.MFDS, serving_g=250, energy_kcal=450, carb_g=90, sugar_g=25, protein_g=8, fat_g=5, is_high_gi=True),
    Food(name="토마토", source=FoodSource.MFDS, serving_g=150, energy_kcal=30, carb_g=6, sugar_g=4, protein_g=1.5, fat_g=0.3, vit_c_mg=20),
    Food(name="김치찌개", source=FoodSource.MFDS, serving_g=400, energy_kcal=320, carb_g=15, sugar_g=5, protein_g=20, fat_g=18, sat_fat_g=6),
    Food(name="고등어", source=FoodSource.MFDS, serving_g=150, energy_kcal=250, carb_g=0, sugar_g=0, protein_g=28, fat_g=15, omega3_mg=1200, zinc_mg=1.1),
    Food(name="브로콜리", source=FoodSource.MFDS, serving_g=100, energy_kcal=35, carb_g=7, sugar_g=2, protein_g=3, fat_g=0.4, vit_c_mg=90),
    Food(name="아몬드", source=FoodSource.MFDS, serving_g=30, energy_kcal=170, carb_g=6, sugar_g=1, protein_g=6, fat_g=15, vit_e_mg=7.5),
    Food(name="굴", source=FoodSource.MFDS, serving_g=100, energy_kcal=70, carb_g=4, sugar_g=0, protein_g=9, fat_g=2, zinc_mg=16),
    Food(name="달걀", source=FoodSource.MFDS, serving_g=50, energy_kcal=75, carb_g=0.5, sugar_g=0.5, protein_g=6, fat_g=5, zinc_mg=0.6),
]

INGREDIENTS = [
    Ingredient(name="연어", key_nutrient="OMEGA3", purpose_tag="오메가3 보충", search_keyword="생연어 필렛", is_primary=True, price_band=PriceBand.HIGH),
    Ingredient(name="고등어", key_nutrient="OMEGA3", purpose_tag="오메가3 보충", search_keyword="국내산 고등어", is_primary=False, price_band=PriceBand.LOW, appeal_note="가격 부담이 낮아요"),
    Ingredient(name="들기름", key_nutrient="OMEGA3", purpose_tag="오메가3 보충", search_keyword="들기름", is_primary=False, price_band=PriceBand.MID, appeal_note="조리 없이 간편해요"),
    Ingredient(name="브로콜리", key_nutrient="VIT_C", purpose_tag="비타민C 보충", search_keyword="유기농 브로콜리", is_primary=True, price_band=PriceBand.LOW),
    Ingredient(name="파프리카", key_nutrient="VIT_C", purpose_tag="비타민C 보충", search_keyword="파프리카", is_primary=False, price_band=PriceBand.LOW, appeal_note="생으로 먹기 편해요"),
    Ingredient(name="키위", key_nutrient="VIT_C", purpose_tag="비타민C 보충", search_keyword="키위", is_primary=False, price_band=PriceBand.LOW, appeal_note="간식으로 먹기 좋아요"),
    Ingredient(name="아몬드", key_nutrient="VIT_E", purpose_tag="비타민E 보충", search_keyword="아몬드", is_primary=True, price_band=PriceBand.MID),
    Ingredient(name="아보카도", key_nutrient="VIT_E", purpose_tag="비타민E 보충", search_keyword="아보카도", is_primary=False, price_band=PriceBand.MID, appeal_note="샐러드에 곁들이기 좋아요"),
    Ingredient(name="해바라기씨", key_nutrient="VIT_E", purpose_tag="비타민E 보충", search_keyword="해바라기씨", is_primary=False, price_band=PriceBand.LOW, appeal_note="간편하게 먹기 좋아요"),
    Ingredient(name="굴", key_nutrient="ZINC", purpose_tag="아연 보충", search_keyword="생굴", is_primary=True, price_band=PriceBand.HIGH),
    Ingredient(name="달걀", key_nutrient="ZINC", purpose_tag="아연 보충", search_keyword="달걀", is_primary=False, price_band=PriceBand.LOW, appeal_note="가장 쉽게 구할 수 있어요"),
    Ingredient(name="견과류", key_nutrient="ZINC", purpose_tag="아연 보충", search_keyword="혼합 견과류", is_primary=False, price_band=PriceBand.MID),
]


def main() -> None:
    db = SessionLocal()
    try:
        if db.query(Food).count() == 0:
            db.add_all(FOODS)
        if db.query(Ingredient).count() == 0:
            db.add_all(INGREDIENTS)
        db.commit()
        print(f"food={db.query(Food).count()}, ingredient={db.query(Ingredient).count()}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
