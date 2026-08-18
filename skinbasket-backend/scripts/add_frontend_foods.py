"""안드로이드 로컬 FoodSeedData.kt(16개)와 백엔드 food 테이블(52개)이 이름 기준으로
겹치는 게 "라면" 하나뿐이었던 문제를 해결하기 위해, 안드로이드에만 있던 나머지 항목을
백엔드에도 추가한다. 이미 이름이 같은 항목(김치찌개/라면/떡볶이)은 건너뛴다.

영양정보는 FoodSeedData.kt에 있던 추정치를 그대로 옮긴 것 — 그 파일 자체 주석에도
"Placeholder nutrition values (estimated, not sourced from the real MFDS DB)"라고
적혀있어 기존 백엔드 52개 데이터와 엄밀함의 수준은 비슷하다.

이름으로 존재 여부를 확인하므로 여러 번 실행해도 안전(idempotent)하다.
실행: (.venv 활성화 후) python scripts/add_frontend_foods.py
"""

from app.db.session import SessionLocal
from app.models.food import Food, FoodSource

NEW_FOODS = [
    Food(name="마라탕", source=FoodSource.MFDS, serving_g=600, energy_kcal=650.0, carb_g=40.0, sugar_g=6.0, protein_g=25.0, fat_g=40.0, sat_fat_g=15.0, vit_c_mg=8.0, zinc_mg=2.0),
    Food(name="치킨", source=FoodSource.MFDS, serving_g=150, energy_kcal=280.0, carb_g=10.0, sugar_g=1.0, protein_g=20.0, fat_g=18.0, sat_fat_g=5.0, zinc_mg=1.2),
    Food(name="피자", source=FoodSource.MFDS, serving_g=150, energy_kcal=285.0, carb_g=33.0, sugar_g=4.0, protein_g=12.0, fat_g=11.0, sat_fat_g=5.0, vit_c_mg=2.0, zinc_mg=1.5, is_dairy=True, is_high_gi=True),
    Food(name="햄버거", source=FoodSource.MFDS, serving_g=250, energy_kcal=550.0, carb_g=45.0, sugar_g=9.0, protein_g=25.0, fat_g=30.0, sat_fat_g=11.0, vit_c_mg=3.0, zinc_mg=4.0, is_dairy=True, is_high_gi=True),
    Food(name="샐러드", source=FoodSource.MFDS, serving_g=250, energy_kcal=150.0, carb_g=12.0, sugar_g=5.0, protein_g=5.0, fat_g=9.0, sat_fat_g=1.5, omega3_mg=200.0, vit_a_ug=300.0, vit_c_mg=25.0, vit_e_mg=2.0, zinc_mg=0.8),
    Food(name="연어", source=FoodSource.MFDS, serving_g=100, energy_kcal=210.0, carb_g=0.0, sugar_g=0.0, protein_g=22.0, fat_g=13.0, sat_fat_g=2.5, omega3_mg=2200.0, vit_a_ug=50.0, vit_e_mg=1.1, zinc_mg=0.5),
    Food(name="고등어", source=FoodSource.MFDS, serving_g=100, energy_kcal=205.0, carb_g=0.0, sugar_g=0.0, protein_g=20.0, fat_g=14.0, sat_fat_g=3.5, omega3_mg=2600.0, vit_a_ug=40.0, vit_e_mg=1.5, zinc_mg=0.7),
    Food(name="브로콜리", source=FoodSource.MFDS, serving_g=100, energy_kcal=34.0, carb_g=7.0, sugar_g=1.7, protein_g=2.8, fat_g=0.4, sat_fat_g=0.1, vit_a_ug=31.0, vit_c_mg=89.0, vit_e_mg=0.8, zinc_mg=0.4),
    Food(name="아몬드", source=FoodSource.MFDS, serving_g=28, energy_kcal=164.0, carb_g=6.0, sugar_g=1.2, protein_g=6.0, fat_g=14.0, sat_fat_g=1.1, vit_e_mg=7.3, zinc_mg=0.9),
    Food(name="키위", source=FoodSource.MFDS, serving_g=76, energy_kcal=42.0, carb_g=10.0, sugar_g=6.0, protein_g=0.8, fat_g=0.4, vit_a_ug=4.0, vit_c_mg=71.0, vit_e_mg=1.0, zinc_mg=0.1),
    Food(name="토마토", source=FoodSource.MFDS, serving_g=123, energy_kcal=22.0, carb_g=4.8, sugar_g=3.2, protein_g=1.1, fat_g=0.2, vit_a_ug=42.0, vit_c_mg=17.0, vit_e_mg=0.5, zinc_mg=0.2),
    Food(name="아보카도 연어 샐러드", source=FoodSource.MFDS, serving_g=300, energy_kcal=320.0, carb_g=12.0, sugar_g=3.0, protein_g=20.0, fat_g=22.0, sat_fat_g=3.0, omega3_mg=1200.0, vit_a_ug=60.0, vit_c_mg=20.0, vit_e_mg=3.0, zinc_mg=0.9),
    Food(name="그릭 요거트와 블루베리", source=FoodSource.MFDS, serving_g=200, energy_kcal=180.0, carb_g=20.0, sugar_g=14.0, protein_g=12.0, fat_g=5.0, sat_fat_g=3.0, vit_a_ug=10.0, vit_c_mg=8.0, vit_e_mg=0.3, zinc_mg=0.8, is_dairy=True),
]


def main() -> None:
    db = SessionLocal()
    try:
        existing_names = {name for (name,) in db.query(Food.name).all()}
        to_add = [f for f in NEW_FOODS if f.name not in existing_names]
        skipped = [f.name for f in NEW_FOODS if f.name in existing_names]
        if to_add:
            db.add_all(to_add)
            db.commit()
        print(f"added={[f.name for f in to_add]}")
        print(f"skipped(already exists)={skipped}")
        print(f"total food count now={db.query(Food).count()}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
