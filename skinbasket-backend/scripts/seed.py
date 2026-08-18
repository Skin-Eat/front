"""시연용 시드 데이터 (food 50 / ingredient 30). AI/데이터 담당자가 준 MySQL INSERT문을
Postgres/SQLAlchemy ORM 형태로 옮긴 것 — 원본은 MySQL 문법(SET NAMES, source='mfds' 소문자
등)이라 그대로 실행 불가능해서 우리 모델 enum(FoodSource.MFDS, PriceBand.*)에 맞게 변환했다.

id는 명시하지 않고 리스트 순서대로 자동증가시킨다 — 원본 SQL의 id 순서와 결과적으로
동일하지만, Postgres 시퀀스가 명시적 id 삽입 때문에 어긋나는 문제를 피하기 위함.
food.name으로 매칭하는 로직(routers/recipes.py 등)만 있고 id를 직접 참조하는 곳은 없어서
안전하다.

주의:
- ingredient의 key_nutrient는 OMEGA3/VIT_C/VIT_E/ZINC 외에 VIT_A/PROTEIN도 포함한다.
  하지만 app/services/skin_score.py(결핍 분석)와 routers/basket.py의 ALL_KEYS는 아직
  4축만 계산한다 — VIT_A/PROTEIN 재료는 DB에는 있지만 /basket/recommendations에는
  당장 안 나타난다. 두 축을 실제로 쓰려면 skin_score.py + basket.py를 같이 확장할 것.
- vit_e_mg가 NULL인 행(족발/순대)은 의도적 결측이다. 0이 아니라 "데이터 없음"으로
  평균 계산에서 제외되는지 확인하는 용도이므로 임의로 값을 채우지 말 것.
- recipe(15종)는 원본 SQL의 테이블 구조(title/user_id/ingredients as {name,amount}/
  generated_by)가 지금 백엔드 모델(name/cooking_time_minutes/servings/ingredients:list[str]/
  steps/skin_benefits) 및 Android RecipeScreen이 이미 쓰고 있는 필드(cookingTimeMinutes,
  servings, skinBenefits)와 안 맞아서 여기 포함하지 않았다. 스키마를 어떻게 합칠지
  팀과 먼저 정할 것 (모델/스키마/라우터/AI 프롬프트 여러 곳에 영향을 준다).

이미 예전 버전(16개/12개)으로 시드해둔 DB가 있다면, food/ingredient 테이블을 비우고
다시 실행해야 이 50/30개 데이터로 교체된다.

실행: (.venv 활성화 후) python scripts/seed.py
"""

from app.db.session import SessionLocal
from app.models.food import Food, FoodSource
from app.models.ingredient import Ingredient, PriceBand

FOODS = [
    # name, serving_g, energy, carb, sugar, protein, fat, sat_fat, omega3, vit_a, vit_c, vit_e, zinc, is_dairy, is_high_gi
    # ── 밥 · 면 · 분식 ──
    Food(name="흰쌀밥", source=FoodSource.MFDS, serving_g=210, energy_kcal=310.00, carb_g=68.50, sugar_g=0.20, protein_g=5.60, fat_g=0.60, sat_fat_g=0.20, omega3_mg=15.00, vit_a_ug=0.00, vit_c_mg=0.00, vit_e_mg=0.10, zinc_mg=1.20, is_dairy=False, is_high_gi=True),
    Food(name="잡곡밥", source=FoodSource.MFDS, serving_g=210, energy_kcal=300.00, carb_g=64.00, sugar_g=0.50, protein_g=7.20, fat_g=1.80, sat_fat_g=0.40, omega3_mg=40.00, vit_a_ug=1.00, vit_c_mg=0.00, vit_e_mg=0.50, zinc_mg=1.80, is_dairy=False, is_high_gi=False),
    Food(name="비빔밥", source=FoodSource.MFDS, serving_g=500, energy_kcal=590.00, carb_g=88.00, sugar_g=8.00, protein_g=21.00, fat_g=16.00, sat_fat_g=4.00, omega3_mg=210.00, vit_a_ug=320.00, vit_c_mg=22.00, vit_e_mg=2.60, zinc_mg=3.20, is_dairy=False, is_high_gi=True),
    Food(name="김치볶음밥", source=FoodSource.MFDS, serving_g=400, energy_kcal=520.00, carb_g=76.00, sugar_g=6.50, protein_g=14.00, fat_g=17.00, sat_fat_g=4.50, omega3_mg=150.00, vit_a_ug=110.00, vit_c_mg=11.00, vit_e_mg=1.80, zinc_mg=2.00, is_dairy=False, is_high_gi=True),
    Food(name="새우볶음밥", source=FoodSource.MFDS, serving_g=400, energy_kcal=500.00, carb_g=72.00, sugar_g=5.00, protein_g=20.00, fat_g=15.00, sat_fat_g=3.50, omega3_mg=260.00, vit_a_ug=85.00, vit_c_mg=6.00, vit_e_mg=2.00, zinc_mg=2.60, is_dairy=False, is_high_gi=True),
    Food(name="김밥", source=FoodSource.MFDS, serving_g=230, energy_kcal=480.00, carb_g=72.00, sugar_g=7.00, protein_g=15.00, fat_g=13.00, sat_fat_g=3.50, omega3_mg=190.00, vit_a_ug=260.00, vit_c_mg=12.00, vit_e_mg=2.20, zinc_mg=1.90, is_dairy=False, is_high_gi=True),
    Food(name="떡볶이", source=FoodSource.MFDS, serving_g=300, energy_kcal=480.00, carb_g=92.00, sugar_g=18.00, protein_g=9.00, fat_g=7.00, sat_fat_g=1.80, omega3_mg=80.00, vit_a_ug=40.00, vit_c_mg=6.00, vit_e_mg=1.00, zinc_mg=1.10, is_dairy=False, is_high_gi=True),
    Food(name="라면", source=FoodSource.MFDS, serving_g=500, energy_kcal=500.00, carb_g=79.00, sugar_g=5.50, protein_g=11.00, fat_g=16.00, sat_fat_g=8.00, omega3_mg=60.00, vit_a_ug=20.00, vit_c_mg=2.00, vit_e_mg=0.90, zinc_mg=1.30, is_dairy=False, is_high_gi=True),
    Food(name="짜장면", source=FoodSource.MFDS, serving_g=650, energy_kcal=700.00, carb_g=110.00, sugar_g=14.00, protein_g=20.00, fat_g=20.00, sat_fat_g=5.50, omega3_mg=130.00, vit_a_ug=30.00, vit_c_mg=8.00, vit_e_mg=1.60, zinc_mg=2.40, is_dairy=False, is_high_gi=True),
    Food(name="짬뽕", source=FoodSource.MFDS, serving_g=700, energy_kcal=600.00, carb_g=88.00, sugar_g=11.00, protein_g=28.00, fat_g=16.00, sat_fat_g=4.50, omega3_mg=300.00, vit_a_ug=120.00, vit_c_mg=20.00, vit_e_mg=2.20, zinc_mg=4.20, is_dairy=False, is_high_gi=True),
    Food(name="냉면", source=FoodSource.MFDS, serving_g=700, energy_kcal=550.00, carb_g=100.00, sugar_g=16.00, protein_g=20.00, fat_g=8.00, sat_fat_g=2.00, omega3_mg=90.00, vit_a_ug=60.00, vit_c_mg=9.00, vit_e_mg=0.80, zinc_mg=2.20, is_dairy=False, is_high_gi=True),
    Food(name="칼국수", source=FoodSource.MFDS, serving_g=700, energy_kcal=520.00, carb_g=84.00, sugar_g=6.00, protein_g=22.00, fat_g=10.00, sat_fat_g=2.50, omega3_mg=140.00, vit_a_ug=55.00, vit_c_mg=8.00, vit_e_mg=1.10, zinc_mg=2.40, is_dairy=False, is_high_gi=True),
    Food(name="콩국수", source=FoodSource.MFDS, serving_g=700, energy_kcal=610.00, carb_g=82.00, sugar_g=7.50, protein_g=26.00, fat_g=20.00, sat_fat_g=3.00, omega3_mg=900.00, vit_a_ug=8.00, vit_c_mg=2.00, vit_e_mg=2.80, zinc_mg=3.00, is_dairy=False, is_high_gi=True),
    # ── 국 · 탕 · 찌개 ──
    Food(name="김치찌개", source=FoodSource.MFDS, serving_g=400, energy_kcal=250.00, carb_g=12.00, sugar_g=5.50, protein_g=18.00, fat_g=14.00, sat_fat_g=4.50, omega3_mg=120.00, vit_a_ug=60.00, vit_c_mg=12.00, vit_e_mg=1.20, zinc_mg=2.10, is_dairy=False, is_high_gi=False),
    Food(name="된장찌개", source=FoodSource.MFDS, serving_g=400, energy_kcal=180.00, carb_g=13.00, sugar_g=4.20, protein_g=13.50, fat_g=8.50, sat_fat_g=2.00, omega3_mg=250.00, vit_a_ug=45.00, vit_c_mg=9.00, vit_e_mg=1.00, zinc_mg=1.60, is_dairy=False, is_high_gi=False),
    Food(name="순두부찌개", source=FoodSource.MFDS, serving_g=400, energy_kcal=230.00, carb_g=10.00, sugar_g=3.80, protein_g=17.00, fat_g=13.00, sat_fat_g=3.20, omega3_mg=300.00, vit_a_ug=55.00, vit_c_mg=8.00, vit_e_mg=1.40, zinc_mg=1.90, is_dairy=False, is_high_gi=False),
    Food(name="부대찌개", source=FoodSource.MFDS, serving_g=450, energy_kcal=480.00, carb_g=38.00, sugar_g=9.50, protein_g=24.00, fat_g=26.00, sat_fat_g=10.50, omega3_mg=180.00, vit_a_ug=90.00, vit_c_mg=10.00, vit_e_mg=1.50, zinc_mg=2.80, is_dairy=True, is_high_gi=True),
    Food(name="미역국", source=FoodSource.MFDS, serving_g=350, energy_kcal=90.00, carb_g=5.00, sugar_g=1.20, protein_g=7.50, fat_g=4.50, sat_fat_g=1.50, omega3_mg=90.00, vit_a_ug=80.00, vit_c_mg=3.00, vit_e_mg=0.60, zinc_mg=0.90, is_dairy=False, is_high_gi=False),
    Food(name="콩나물국", source=FoodSource.MFDS, serving_g=350, energy_kcal=60.00, carb_g=5.50, sugar_g=1.50, protein_g=4.50, fat_g=1.80, sat_fat_g=0.30, omega3_mg=60.00, vit_a_ug=12.00, vit_c_mg=8.00, vit_e_mg=0.40, zinc_mg=0.50, is_dairy=False, is_high_gi=False),
    Food(name="갈비탕", source=FoodSource.MFDS, serving_g=500, energy_kcal=420.00, carb_g=12.00, sugar_g=3.00, protein_g=32.00, fat_g=26.00, sat_fat_g=11.00, omega3_mg=130.00, vit_a_ug=20.00, vit_c_mg=5.00, vit_e_mg=0.70, zinc_mg=5.20, is_dairy=False, is_high_gi=False),
    Food(name="삼계탕", source=FoodSource.MFDS, serving_g=600, energy_kcal=620.00, carb_g=18.00, sugar_g=2.00, protein_g=55.00, fat_g=34.00, sat_fat_g=9.50, omega3_mg=350.00, vit_a_ug=60.00, vit_c_mg=4.00, vit_e_mg=1.60, zinc_mg=3.40, is_dairy=False, is_high_gi=False),
    Food(name="설렁탕", source=FoodSource.MFDS, serving_g=500, energy_kcal=350.00, carb_g=10.00, sugar_g=2.00, protein_g=28.00, fat_g=21.00, sat_fat_g=9.00, omega3_mg=100.00, vit_a_ug=15.00, vit_c_mg=2.00, vit_e_mg=0.50, zinc_mg=4.60, is_dairy=False, is_high_gi=False),
    Food(name="육개장", source=FoodSource.MFDS, serving_g=450, energy_kcal=300.00, carb_g=11.00, sugar_g=3.50, protein_g=24.00, fat_g=17.00, sat_fat_g=6.50, omega3_mg=110.00, vit_a_ug=210.00, vit_c_mg=14.00, vit_e_mg=1.80, zinc_mg=4.00, is_dairy=False, is_high_gi=False),
    Food(name="감자탕", source=FoodSource.MFDS, serving_g=550, energy_kcal=520.00, carb_g=30.00, sugar_g=5.00, protein_g=33.00, fat_g=29.00, sat_fat_g=10.00, omega3_mg=160.00, vit_a_ug=95.00, vit_c_mg=18.00, vit_e_mg=1.90, zinc_mg=4.80, is_dairy=False, is_high_gi=False),
    # ── 고기 · 구이 · 튀김 ──
    Food(name="불고기", source=FoodSource.MFDS, serving_g=250, energy_kcal=420.00, carb_g=14.00, sugar_g=10.00, protein_g=30.00, fat_g=25.00, sat_fat_g=9.50, omega3_mg=120.00, vit_a_ug=25.00, vit_c_mg=6.00, vit_e_mg=0.90, zinc_mg=5.60, is_dairy=False, is_high_gi=False),
    Food(name="제육볶음", source=FoodSource.MFDS, serving_g=250, energy_kcal=480.00, carb_g=16.00, sugar_g=11.00, protein_g=27.00, fat_g=33.00, sat_fat_g=11.00, omega3_mg=150.00, vit_a_ug=70.00, vit_c_mg=14.00, vit_e_mg=1.40, zinc_mg=2.80, is_dairy=False, is_high_gi=False),
    Food(name="삼겹살구이", source=FoodSource.MFDS, serving_g=200, energy_kcal=640.00, carb_g=1.00, sugar_g=0.30, protein_g=34.00, fat_g=55.00, sat_fat_g=20.00, omega3_mg=190.00, vit_a_ug=10.00, vit_c_mg=1.00, vit_e_mg=0.60, zinc_mg=3.00, is_dairy=False, is_high_gi=False),
    Food(name="닭갈비", source=FoodSource.MFDS, serving_g=300, energy_kcal=520.00, carb_g=24.00, sugar_g=12.00, protein_g=34.00, fat_g=30.00, sat_fat_g=8.00, omega3_mg=220.00, vit_a_ug=90.00, vit_c_mg=22.00, vit_e_mg=1.70, zinc_mg=2.60, is_dairy=False, is_high_gi=False),
    Food(name="닭볶음탕", source=FoodSource.MFDS, serving_g=400, energy_kcal=480.00, carb_g=22.00, sugar_g=8.50, protein_g=36.00, fat_g=26.00, sat_fat_g=7.00, omega3_mg=250.00, vit_a_ug=70.00, vit_c_mg=26.00, vit_e_mg=1.50, zinc_mg=2.70, is_dairy=False, is_high_gi=False),
    Food(name="후라이드치킨", source=FoodSource.MFDS, serving_g=250, energy_kcal=700.00, carb_g=34.00, sugar_g=1.50, protein_g=40.00, fat_g=44.00, sat_fat_g=11.00, omega3_mg=320.00, vit_a_ug=30.00, vit_c_mg=0.00, vit_e_mg=4.20, zinc_mg=2.40, is_dairy=False, is_high_gi=True),
    Food(name="양념치킨", source=FoodSource.MFDS, serving_g=250, energy_kcal=730.00, carb_g=52.00, sugar_g=22.00, protein_g=37.00, fat_g=40.00, sat_fat_g=10.00, omega3_mg=300.00, vit_a_ug=45.00, vit_c_mg=2.00, vit_e_mg=4.00, zinc_mg=2.30, is_dairy=False, is_high_gi=True),
    Food(name="돈까스", source=FoodSource.MFDS, serving_g=200, energy_kcal=590.00, carb_g=38.00, sugar_g=4.00, protein_g=28.00, fat_g=36.00, sat_fat_g=9.00, omega3_mg=260.00, vit_a_ug=25.00, vit_c_mg=3.00, vit_e_mg=3.60, zinc_mg=2.20, is_dairy=False, is_high_gi=True),
    Food(name="보쌈", source=FoodSource.MFDS, serving_g=250, energy_kcal=520.00, carb_g=8.00, sugar_g=3.00, protein_g=38.00, fat_g=38.00, sat_fat_g=13.50, omega3_mg=170.00, vit_a_ug=55.00, vit_c_mg=20.00, vit_e_mg=0.80, zinc_mg=3.40, is_dairy=False, is_high_gi=False),
    Food(name="족발", source=FoodSource.MFDS, serving_g=250, energy_kcal=550.00, carb_g=6.00, sugar_g=2.50, protein_g=42.00, fat_g=40.00, sat_fat_g=14.00, omega3_mg=160.00, vit_a_ug=12.00, vit_c_mg=2.00, vit_e_mg=None, zinc_mg=3.20, is_dairy=False, is_high_gi=False),
    Food(name="순대", source=FoodSource.MFDS, serving_g=200, energy_kcal=380.00, carb_g=44.00, sugar_g=2.00, protein_g=14.00, fat_g=16.00, sat_fat_g=6.00, omega3_mg=90.00, vit_a_ug=8.00, vit_c_mg=1.00, vit_e_mg=None, zinc_mg=3.80, is_dairy=False, is_high_gi=True),
    Food(name="김치만두", source=FoodSource.MFDS, serving_g=200, energy_kcal=420.00, carb_g=48.00, sugar_g=4.00, protein_g=16.00, fat_g=17.00, sat_fat_g=6.00, omega3_mg=140.00, vit_a_ug=40.00, vit_c_mg=9.00, vit_e_mg=1.40, zinc_mg=1.80, is_dairy=False, is_high_gi=True),
    # ── 생선 · 해산물 ──
    Food(name="고등어구이", source=FoodSource.MFDS, serving_g=150, energy_kcal=320.00, carb_g=0.50, sugar_g=0.00, protein_g=30.00, fat_g=22.00, sat_fat_g=5.50, omega3_mg=3200.00, vit_a_ug=35.00, vit_c_mg=1.00, vit_e_mg=2.40, zinc_mg=1.40, is_dairy=False, is_high_gi=False),
    Food(name="갈치구이", source=FoodSource.MFDS, serving_g=150, energy_kcal=240.00, carb_g=0.30, sugar_g=0.00, protein_g=26.00, fat_g=15.00, sat_fat_g=4.00, omega3_mg=1800.00, vit_a_ug=30.00, vit_c_mg=1.00, vit_e_mg=1.60, zinc_mg=1.00, is_dairy=False, is_high_gi=False),
    Food(name="연어구이", source=FoodSource.MFDS, serving_g=150, energy_kcal=310.00, carb_g=0.40, sugar_g=0.00, protein_g=32.00, fat_g=19.00, sat_fat_g=3.80, omega3_mg=3400.00, vit_a_ug=20.00, vit_c_mg=2.00, vit_e_mg=2.80, zinc_mg=0.90, is_dairy=False, is_high_gi=False),
    Food(name="생굴무침", source=FoodSource.MFDS, serving_g=120, energy_kcal=110.00, carb_g=6.00, sugar_g=2.00, protein_g=10.00, fat_g=3.00, sat_fat_g=0.80, omega3_mg=700.00, vit_a_ug=45.00, vit_c_mg=14.00, vit_e_mg=1.20, zinc_mg=18.50, is_dairy=False, is_high_gi=False),
    Food(name="오징어볶음", source=FoodSource.MFDS, serving_g=250, energy_kcal=300.00, carb_g=18.00, sugar_g=8.00, protein_g=28.00, fat_g=13.00, sat_fat_g=2.50, omega3_mg=600.00, vit_a_ug=60.00, vit_c_mg=22.00, vit_e_mg=3.00, zinc_mg=3.20, is_dairy=False, is_high_gi=False),
    Food(name="멸치볶음", source=FoodSource.MFDS, serving_g=40, energy_kcal=130.00, carb_g=6.00, sugar_g=3.00, protein_g=12.00, fat_g=6.00, sat_fat_g=1.50, omega3_mg=450.00, vit_a_ug=20.00, vit_c_mg=0.00, vit_e_mg=1.00, zinc_mg=1.60, is_dairy=False, is_high_gi=False),
    Food(name="해물파전", source=FoodSource.MFDS, serving_g=250, energy_kcal=480.00, carb_g=52.00, sugar_g=5.00, protein_g=20.00, fat_g=22.00, sat_fat_g=4.00, omega3_mg=500.00, vit_a_ug=90.00, vit_c_mg=18.00, vit_e_mg=3.40, zinc_mg=2.60, is_dairy=False, is_high_gi=True),
    # ── 반찬 · 채소 · 달걀 · 두부 ──
    Food(name="잡채", source=FoodSource.MFDS, serving_g=200, energy_kcal=320.00, carb_g=46.00, sugar_g=9.00, protein_g=9.00, fat_g=11.00, sat_fat_g=2.50, omega3_mg=130.00, vit_a_ug=180.00, vit_c_mg=16.00, vit_e_mg=1.90, zinc_mg=1.20, is_dairy=False, is_high_gi=True),
    Food(name="두부김치", source=FoodSource.MFDS, serving_g=250, energy_kcal=330.00, carb_g=12.00, sugar_g=4.50, protein_g=22.00, fat_g=21.00, sat_fat_g=6.00, omega3_mg=380.00, vit_a_ug=65.00, vit_c_mg=13.00, vit_e_mg=1.60, zinc_mg=2.40, is_dairy=False, is_high_gi=False),
    Food(name="계란말이", source=FoodSource.MFDS, serving_g=150, energy_kcal=240.00, carb_g=4.00, sugar_g=2.00, protein_g=16.00, fat_g=18.00, sat_fat_g=5.00, omega3_mg=190.00, vit_a_ug=250.00, vit_c_mg=3.00, vit_e_mg=2.10, zinc_mg=1.60, is_dairy=False, is_high_gi=False),
    Food(name="계란찜", source=FoodSource.MFDS, serving_g=200, energy_kcal=190.00, carb_g=3.50, sugar_g=1.80, protein_g=15.00, fat_g=13.00, sat_fat_g=4.00, omega3_mg=160.00, vit_a_ug=230.00, vit_c_mg=2.00, vit_e_mg=1.70, zinc_mg=1.50, is_dairy=False, is_high_gi=False),
    Food(name="시금치나물", source=FoodSource.MFDS, serving_g=100, energy_kcal=70.00, carb_g=4.50, sugar_g=1.00, protein_g=4.00, fat_g=4.00, sat_fat_g=0.60, omega3_mg=130.00, vit_a_ug=480.00, vit_c_mg=25.00, vit_e_mg=2.30, zinc_mg=0.70, is_dairy=False, is_high_gi=False),
    # ── 유제품 ──
    Food(name="플레인 요거트(무가당)", source=FoodSource.MFDS, serving_g=200, energy_kcal=130.00, carb_g=12.00, sugar_g=11.00, protein_g=9.00, fat_g=5.00, sat_fat_g=3.20, omega3_mg=40.00, vit_a_ug=55.00, vit_c_mg=1.00, vit_e_mg=0.20, zinc_mg=1.20, is_dairy=True, is_high_gi=False),
    Food(name="우유(200ml)", source=FoodSource.MFDS, serving_g=200, energy_kcal=130.00, carb_g=9.60, sugar_g=9.00, protein_g=6.60, fat_g=6.80, sat_fat_g=4.40, omega3_mg=30.00, vit_a_ug=68.00, vit_c_mg=2.00, vit_e_mg=0.20, zinc_mg=0.80, is_dairy=True, is_high_gi=False),
]

INGREDIENTS = [
    # OMEGA3 (항염 — acne 고민 축)
    Ingredient(name="연어", key_nutrient="OMEGA3", purpose_tag="오메가3 보충", search_keyword="생연어 필렛", is_primary=True, price_band=PriceBand.HIGH),
    Ingredient(name="고등어", key_nutrient="OMEGA3", purpose_tag="오메가3 보충", search_keyword="손질 고등어", is_primary=False, price_band=PriceBand.LOW, appeal_note="가격 부담이 낮아요"),
    Ingredient(name="들기름", key_nutrient="OMEGA3", purpose_tag="오메가3 보충", search_keyword="국산 생들기름", is_primary=False, price_band=PriceBand.MID, appeal_note="조리 없이 나물에 두르기만 하면 돼요"),
    Ingredient(name="호두", key_nutrient="OMEGA3", purpose_tag="오메가3 보충", search_keyword="생호두 깐호두", is_primary=False, price_band=PriceBand.MID, appeal_note="간식으로 챙겨 먹기 좋아요"),
    Ingredient(name="아마씨", key_nutrient="OMEGA3", purpose_tag="오메가3 보충", search_keyword="볶은 아마씨 분말", is_primary=False, price_band=PriceBand.LOW, appeal_note="요거트에 뿌리면 끝이에요"),
    # VIT_A (장벽 재생 · pigmentation 축) — 주의: skin_score.py/basket.py는 아직 이 축을 안 씀
    Ingredient(name="당근", key_nutrient="VIT_A", purpose_tag="비타민A 보충", search_keyword="흙당근", is_primary=True, price_band=PriceBand.LOW),
    Ingredient(name="단호박", key_nutrient="VIT_A", purpose_tag="비타민A 보충", search_keyword="미니 단호박", is_primary=False, price_band=PriceBand.LOW, appeal_note="찌기만 해도 한 끼가 돼요"),
    Ingredient(name="시금치", key_nutrient="VIT_A", purpose_tag="비타민A 보충", search_keyword="손질 시금치", is_primary=False, price_band=PriceBand.LOW, appeal_note="데치면 한 줌으로 확 줄어 많이 먹기 쉬워요"),
    Ingredient(name="김", key_nutrient="VIT_A", purpose_tag="비타민A 보충", search_keyword="구운 김 조미김", is_primary=False, price_band=PriceBand.LOW, appeal_note="밥반찬으로 매일 챙기기 쉬워요"),
    Ingredient(name="고구마", key_nutrient="VIT_A", purpose_tag="비타민A 보충", search_keyword="베니하루카 고구마", is_primary=False, price_band=PriceBand.MID, appeal_note="아침 대용으로 든든해요"),
    # VIT_C (항산화 · 콜라겐 합성)
    Ingredient(name="브로콜리", key_nutrient="VIT_C", purpose_tag="비타민C 보충", search_keyword="생브로콜리", is_primary=True, price_band=PriceBand.LOW),
    Ingredient(name="파프리카", key_nutrient="VIT_C", purpose_tag="비타민C 보충", search_keyword="컬러 파프리카", is_primary=False, price_band=PriceBand.LOW, appeal_note="생으로 먹기 편해요"),
    Ingredient(name="키위", key_nutrient="VIT_C", purpose_tag="비타민C 보충", search_keyword="골드키위", is_primary=False, price_band=PriceBand.MID, appeal_note="껍질만 벗기면 바로 먹어요"),
    Ingredient(name="딸기", key_nutrient="VIT_C", purpose_tag="비타민C 보충", search_keyword="설향 딸기", is_primary=False, price_band=PriceBand.HIGH, appeal_note="단맛이 강해 디저트 대신 좋아요"),
    Ingredient(name="방울토마토", key_nutrient="VIT_C", purpose_tag="비타민C 보충", search_keyword="대추방울토마토", is_primary=False, price_band=PriceBand.LOW, appeal_note="씻어서 통째로 먹을 수 있어요"),
    # VIT_E (항산화 · 유분 밸런스)
    Ingredient(name="아몬드", key_nutrient="VIT_E", purpose_tag="비타민E 보충", search_keyword="생아몬드 무염", is_primary=True, price_band=PriceBand.MID),
    Ingredient(name="해바라기씨", key_nutrient="VIT_E", purpose_tag="비타민E 보충", search_keyword="볶은 해바라기씨", is_primary=False, price_band=PriceBand.LOW, appeal_note="같은 값에 비타민E가 가장 많아요"),
    Ingredient(name="아보카도", key_nutrient="VIT_E", purpose_tag="비타민E 보충", search_keyword="완숙 아보카도", is_primary=False, price_band=PriceBand.MID, appeal_note="빵이나 밥에 얹기만 해도 돼요"),
    Ingredient(name="엑스트라버진 올리브오일", key_nutrient="VIT_E", purpose_tag="비타민E 보충", search_keyword="엑스트라버진 올리브오일", is_primary=False, price_band=PriceBand.MID, appeal_note="샐러드에 두르는 것으로 충분해요"),
    Ingredient(name="잣", key_nutrient="VIT_E", purpose_tag="비타민E 보충", search_keyword="국산 잣", is_primary=False, price_band=PriceBand.HIGH, appeal_note="나물이나 죽에 조금만 넣어도 향이 살아요"),
    # ZINC (피지 조절 · 상처 회복)
    Ingredient(name="굴", key_nutrient="ZINC", purpose_tag="아연 보충", search_keyword="생굴 봉지굴", is_primary=True, price_band=PriceBand.HIGH),
    Ingredient(name="호박씨", key_nutrient="ZINC", purpose_tag="아연 보충", search_keyword="볶은 호박씨", is_primary=False, price_band=PriceBand.LOW, appeal_note="비린 맛 없이 아연을 챙길 수 있어요"),
    Ingredient(name="바지락", key_nutrient="ZINC", purpose_tag="아연 보충", search_keyword="해감 바지락", is_primary=False, price_band=PriceBand.LOW, appeal_note="국 하나만 끓여도 채워져요"),
    Ingredient(name="캐슈너트", key_nutrient="ZINC", purpose_tag="아연 보충", search_keyword="생캐슈넛 무염", is_primary=False, price_band=PriceBand.MID, appeal_note="고소해서 간식으로 부담이 없어요"),
    Ingredient(name="렌틸콩", key_nutrient="ZINC", purpose_tag="아연 보충", search_keyword="렌틸콩 렌틸", is_primary=False, price_band=PriceBand.LOW, appeal_note="밥에 섞어 지으면 손이 안 가요"),
    # PROTEIN (장벽 · 수분) — 주의: skin_score.py/basket.py는 아직 이 축을 안 씀
    Ingredient(name="두부", key_nutrient="PROTEIN", purpose_tag="단백질 보충", search_keyword="국산콩 부침두부", is_primary=True, price_band=PriceBand.LOW),
    Ingredient(name="달걀", key_nutrient="PROTEIN", purpose_tag="단백질 보충", search_keyword="무항생제 계란", is_primary=False, price_band=PriceBand.LOW, appeal_note="어떤 끼니에도 얹을 수 있어요"),
    Ingredient(name="닭가슴살", key_nutrient="PROTEIN", purpose_tag="단백질 보충", search_keyword="생닭가슴살", is_primary=False, price_band=PriceBand.MID, appeal_note="포화지방이 적어 부담이 없어요"),
    Ingredient(name="그릭요거트", key_nutrient="PROTEIN", purpose_tag="단백질 보충", search_keyword="무가당 그릭요거트", is_primary=False, price_band=PriceBand.MID, appeal_note="조리 없이 바로 먹어요"),
    Ingredient(name="병아리콩", key_nutrient="PROTEIN", purpose_tag="단백질 보충", search_keyword="병아리콩 삶은", is_primary=False, price_band=PriceBand.LOW, appeal_note="식물성으로 채우고 싶을 때 좋아요"),
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
