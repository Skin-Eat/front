# Skin Basket Backend (FastAPI + Supabase)

**배포 구조: Vercel(프론트) → 가비아(이 FastAPI 백엔드, `deploy/` 참고) → Supabase(DB+Auth).**
DB는 Supabase Postgres, 로그인/회원가입(인증)도 같은 Supabase 프로젝트의 Supabase Auth를
쓴다 — 가비아는 이 FastAPI 앱을 올려두는 서버일 뿐, DB는 안 갖고 있다(한때 DB만 가비아
MySQL로 분리하는 안을 검토했었지만 다시 Supabase로 통합함).

Skin Basket 해커톤 프로젝트의 백엔드. API 명세가 아직 확정 전이라 **구조(기반)를 먼저
잡고, 세부 스펙은 라우터/스키마 파일 단위로 계속 갈아끼울 수 있게** 설계했다.
Android 프론트(`../lionideaton`)는 건드리지 않는다는 전제로, 프론트가 이미 하드코딩해둔
계약(`POST /ai/food-image`의 요청/응답 shape)만 정확히 맞춰서 구현했다.

## 구조

```
app/
  core/       설정(config.py), Supabase JWT 인증(security.py) — 자주 안 바뀜
  db/         SQLAlchemy 세션/Base — 안 바뀜
  models/     SQLAlchemy 테이블 정의 (DRAFT, DB 설계 문서 v0.3와 대조 필요)
  schemas/    Pydantic 요청/응답 모델 — API 명세 바뀌면 여기부터 고침
  services/   규칙 기반 점수 계산, OpenAI API 클라이언트 — 로직 본체
  routers/    엔드포인트 — API 명세 바뀌면 여기 다음으로 고침
  main.py     라우터 등록 + CORS
alembic/      DB 마이그레이션
scripts/seed.py  로컬 테스트용 최소 시드 데이터 (Android 시드와 이름 맞춤)
deploy/       가비아 g클라우드 배포용 systemd/nginx 설정 + 체크리스트 (deploy/DEPLOY.md)
```

**API 명세가 바뀔 때 손댈 순서**: `schemas/*.py` (필드 추가/변경) → `routers/*.py` (엔드포인트
로직) → 필요하면 `models/*.py` (테이블 컬럼) → `alembic revision --autogenerate` 로 마이그레이션
생성. `core/`, `db/`, `main.py`는 거의 안 건드려도 됨.

## 지금 구현된 것 / 안 된 것

| 도메인 | 상태 |
|---|---|
| 인증 (`POST /auth/signup`, `POST /auth/login`, `/users/me*`) | API 명세서 v2 반영: 프론트는 Supabase를 모르고 우리 API만 씀. 백엔드가 Supabase Auth를 서버사이드에서 대신 호출(`services/supabase_auth.py`)하고 그 accessToken을 그대로 돌려줌. **실제 회원가입~로그인~`/meals` 등록~`/analysis/diet` 반영까지 실기기로 전 과정 검증 완료.** 이 과정에서 이 Supabase 프로젝트가 레거시 HS256이 아니라 **비대칭키(ES256)로 토큰을 발급한다는 걸 확인**해서 `security.py`를 JWKS(`/auth/v1/.well-known/jwks.json`) 검증 방식으로 다시 짬 (alg를 보고 HS256/그외 자동 분기, 둘 다 지원). Supabase 프로젝트의 이메일 확인(Confirm email)은 꺼져 있어야 함(껐음) — 켜져 있으면 가입 응답에 accessToken이 없어서 실패함 |
| 식사 기록 (`/meals`) | 등록(끼니당 여러 항목)/조회(`from`,`to`)/수정/삭제, `POST /meals/analyze-photo` |
| 분석 (`/analysis/diet`) | Android `SkinScoreCalculator`(결핍 분석 + 점수 계산 둘 다) 이식, 최근 7일(가변) 기준, 저장 안 함 |
| 추천 (`/recommendations/ingredients`) | 부족 축 기반 주재료+보충옵션 반환 (최대 3그룹, subs 최대 3) |
| 장보기 (`/basket`, `/basket/items`) | 새 `basket_item` 테이블로 영속화 |
| 레시피 (`/recipes`, `/recipes/{id}`, `POST /recipes/generate`, `POST /recipes/{id}/eat`) | generate는 DB 큐레이션 레시피 매칭(AI 생성 아님). eat는 폐쇄 루프의 핵심 — 레시피 재료명(`ingredients[].name`)을 food 테이블과 이름 매칭해 자동으로 식사 기록을 만듦 (매칭 방식은 추후 ID 매핑으로 교체 권장). **recipe 15종 시드 데이터는 AI 담당자 SQL에 `cooking_time_minutes`/`servings`/`skin_benefits`가 없어서 아직 미반영 — 값 받으면 `scripts/seed.py`에 추가할 것, 그때까지 recipe 테이블은 비어있음** |
| 피부 기록 (`/skin-logs`) | 등록/조회 동작. 사진은 URL만 받음(Supabase Storage에 프론트가 직접 업로드한다는 전제) |
| 쇼핑 검색 | **백엔드에 없음.** 네이버 쇼핑검색 오픈API(`/v1/search/shop.json`)가 2026-07-31부로 완전 종료되고 공식 대체 API가 없음을 확인함. 쿠팡/컬리와 동일한 원칙(구매자용 쓰기 API 없음 → 프론트 딥링크)을 그대로 적용 — 프론트가 `https://msearch.shopping.naver.com/search/all?query=...` 같은 검색 결과 페이지를 여는 방식으로 처리 |
| AI 사진 인식 (`POST /ai/food-image`) | OpenAI(`gpt-4.1-mini`, 비전) 호출, food 테이블에서 뽑은 후보 안에서만 고르게 프롬프트 강제. `OPENAI_API_KEY` 없으면 502. 모델·프롬프트는 AI 담당자가 실제 사진 24장으로 검증한 결과(23/24=95.8%, `Skin-Eat/ai` 레포 참고)를 반영함 — `gpt-4o-mini`는 저티어 계정 일일 한도(RPD)에 걸려서 `gpt-4.1-mini`로 교체 |
| AI 분석 코멘트 (`POST /ai/analysis-comment`) | **DRAFT.** 결핍 분석을 자연어 코멘트로 변환. 동작은 하지만 경로/응답 shape 미확정 — 프론트 확정 전까지 바뀔 수 있음 |
| AI 레시피 생성 (`POST /ai/recipe-suggestion`) | **DRAFT.** recipe 테이블 대신 부족 영양소/알레르기·비선호를 반영해 즉석 생성. 저장 여부·food 테이블 매칭 방식 미정 — `app/services/openai_client.py` docstring 참고 |
| 쿠팡/컬리/네이버쇼핑 연동 | 안 함 — 구매자용 쓰기 API가 없거나(쿠팡/컬리) 검색 API가 종료돼서(네이버) 셋 다 프론트가 딥링크 버튼으로 처리 |
| 점수 저장/캐싱 | 안 함 — 항상 조회 시점 계산 (공통 지침 확정 사항) |

## API 명세서 v2 (프론트 작성) 반영 현황

프론트 개발자가 정리한 API 명세서 v2를 기준으로 진행 중. 공통 규약 두 가지부터 먼저 반영함:

- **응답 봉투**: 모든 응답을 `{success, data, error}`로 감싼다. `app/core/envelope.py`의
  `EnvelopeRoute`(라우터별로 `route_class=EnvelopeRoute` 지정)가 자동으로 감싸고,
  `main.py`의 예외 핸들러가 에러도 같은 형식으로 반환. **단, `/ai/food-image`는 예외** —
  안드로이드가 이미 하드코딩한 구 계약이라 봉투 없이 예전 shape 그대로 유지 (아래 참고).
- **camelCase**: 명세서가 `skinType`/`photoConsent`/`accessToken`처럼 camelCase를 쓰므로,
  `app/schemas/base.py`의 `CamelModel`을 상속하면 자동 변환됨. 이제 거의 모든 스키마가
  이걸 씀 — `FoodImageAnalysisResponse`(안드로이드 구 계약이라 의도적으로 예외)만 남음.

**반영 완료 (DB로 실제 검증까지 함):**
- `POST /auth/signup`, `POST /auth/login`, `/users/me*`(GET/PATCH, constraints CRUD). `ConstraintType` 값도 소문자로(`allergy`/`dislike`) — enum 멤버 이름은 그대로라 DB 마이그레이션 불필요
- `POST/GET/PATCH/DELETE /meals` — 끼니당 여러 항목, `isAiDetected`, `from`/`to` 조회
- `POST /meals/analyze-photo` — `/ai/food-image`의 신규 버전(신규 추가, 구버전은 안드로이드 호환 위해 그대로 둠). 응답이 `candidates:[문자열]` 대신 `detected:[{foodId,name,portionRatio}]`이고, AI 인식 실패를 502가 아니라 `success:true + aiFailed:true`로 표현(명세서 0번 공통 규약)
- `GET /analysis/diet?days=` — Android `SkinScoreCalculator.scoreForItem`도 이번에 같이 포팅함(그동안 결핍 분석만 있고 점수 자체가 없었음). `score.total`/`axes`/`deficiencies[].ratio,priority`/`summary` 전부 실제 데이터 기반
- `GET /recommendations/ingredients` — 예전 `/basket/recommendations`를 이 경로로 옮기고 "최대 3그룹, primary 1 + supplements 최대 3" 캡 적용. 부족이 없을 때 4축 전부 보여주던 기존 규칙과 "최대 3개"가 충돌해서, 부족 없을 때도 임계값에 가장 가까운 3축만 보여주는 쪽으로 정리함(축 하나가 안 보일 수 있다는 뜻 — Android 쪽 화면과 다시 맞춰볼 것)
- `GET /basket`, `POST/PATCH/DELETE /basket/items`(+전체비우기) — 새 `basket_item` 테이블로 영속화
- `GET /recipes`, `POST /recipes/generate`, `POST /recipes/{id}/eat`(바디로 eatenAt/mealType/portionRatio 받음) — **`/recipes/generate`는 AI로 새로 만들지 않고 DB의 큐레이션 레시피 중 `ingredientIds`와 재료가 가장 많이 겹치는 걸 찾아 반환함(매칭), 겹치는 게 없으면 isFallback=true.** (처음엔 "LLM 생성 실패 시 폴백"이라는 명세서 문구를 "기본은 AI 생성"으로 오독해서 AI 생성 버전으로 만들었다가, 원래 계획이 DB 매칭이라는 걸 확인하고 수정함 — AI 생성 코드는 제거함)
- `GET/POST /foods` — 검색/직접 추가(`FoodSource.USER_ADDED`) 신규
- `POST/GET/DELETE /skin-logs` — `from`/`to` 조회, `DELETE` 추가, level 1~5 검증

**아직 명세서와 안 맞는 것 / 확인 필요:**
- **`GET /shopping/products` 충돌**: 명세서는 "네이버 쇼핑 프록시, 백엔드 필수 경유"를 전제로 하는데, 네이버 쇼핑검색 API는 이미 종료돼서 대체 API가 없다는 걸 이 프로젝트에서 이미 확인함 (위 "쇼핑 검색" 항목 참고) — **프론트 개발자에게 전달 필요(아직 미전달)**, 명세서에서 이 엔드포인트는 빼야 함
- `/ai/recipe-suggestion`, `/ai/analysis-comment`(DRAFT) — 명세서에 없는 엔드포인트. AI 3역할 중 ②③으로 만들어뒀던 것들인데 ④ 요리는 DB 매칭으로 확정됐으니, 이 두 개도 계속 쓸지(다른 화면용?) 아니면 정리할지 팀 확인 필요
- `/meals`, `PATCH /users/me` 등은 명세서에 없던 유효성 검증(portionRatio 0~10, level 1~5 등)을 Pydantic `Field`로 추가함 — 서버가 400으로 막아주는 항목이라 프론트에서 별도로 안 막아도 됨
- `recipe` 테이블이 아직 비어있어서(15종 시드 데이터 값 대기 중, 위 레시피 항목 참고) `GET /recipes`, `POST /recipes/generate`가 실제로는 항상 빈 목록/404를 반환함 — 시드 채워지면 바로 동작

### 쇼핑 연동의 확장 가능성 (발표용 근거)

지금은 딥링크(단순 검색 페이지 열기)뿐이라 "그냥 사이트만 띄워주는 거 아니냐"는 질문이
나올 수 있음. 근거: **쿠팡 파트너스 Open API**(developers.coupang.com)에 실제로
① 상품검색 API(상품명/가격/이미지 반환, 키워드 검색) ② 딥링크 생성 API(일반 링크를
커미션이 발생하는 제휴 링크로 변환)가 존재함을 확인함 — 즉 지금 구조는 이후 이 두
API로 그대로 업그레이드되는 자리이고, 단순 UX 개선이 아니라 **서비스 자체의 수익
모델(제휴 커미션)로 이어지는 확장 포인트**.

다만 파트너스 API는 가입만으로 안 풀리고 최근 판매 실적 조건이 있어 해커톤 기간 내
활성화는 불가능 — 그래서 지금 신청하지는 않았고, 대신 API 스펙/제약을 미리 조사해서
구체적인 확장 경로로 근거만 남겨둔 상태.

## 로컬 세팅

```bash
python -m venv .venv
.venv\Scripts\activate          # (Windows)
pip install -r requirements.txt
copy .env.example .env          # 값 채우기 (아래 참고)
```

`.env`에서 채울 것:
- `DATABASE_URL`: Supabase 프로젝트 > Settings > Database > Connection string (Session pooler 권장)
- `SUPABASE_URL`, `SUPABASE_JWT_SECRET`: Settings > API (DB랑 같은 프로젝트)
- `SUPABASE_ANON_KEY`: Settings > API Keys의 **anon public** 키 (service_role 아님) — `/auth/signup`, `/auth/login`이 Supabase Auth를 대신 호출할 때 씀
- `OPENAI_API_KEY`: 안 채우면 AI 기능만 502, 나머지는 정상 동작
- `APP_ENV`: 로컬은 기본값 `local` 그대로 두면 됨. 배포/데모 환경에서는 `production` 등으로
  바꿔야 `SUPABASE_JWT_SECRET` 미설정 시 인증이 뚫리는 개발용 폴백이 막힌다 (`app/core/security.py`).

## DB 마이그레이션

```bash
alembic revision --autogenerate -m "init"
alembic upgrade head
python scripts/seed.py     # 최소 시드 데이터 (food/ingredient)
```

Supabase는 테이블을 Table Editor로 직접 만들 수도 있지만, 팀이 스키마를 계속 바꿀
예정이라 **alembic으로 버전 관리하는 걸 권장** — `models/*.py`만 고치고 autogenerate하면 됨.

## 실행

```bash
uvicorn app.main:app --reload --port 8000
```

- Swagger 문서: http://localhost:8000/docs
- 헬스체크: http://localhost:8000/health
- 안드로이드 에뮬레이터에서 접속 시 `NetworkModule.BASE_URL`이 이미 `http://10.0.2.2:8000/`로
  맞춰져 있음 — 포트를 8000 이외로 바꾸면 프론트에도 알릴 것.

## 인증 방식 (결정됨)

API 명세서 v2 기준으로 확정: **프론트는 Supabase 존재 자체를 모르고 `POST /auth/signup`,
`POST /auth/login`만 호출한다.** 백엔드가 그 요청을 받아 Supabase Auth REST API를
서버사이드에서 대신 호출하고(`app/services/supabase_auth.py`), 거기서 받은 accessToken을
그대로 돌려준다. 그 토큰은 Supabase가 발급한 진짜 JWT라서 `app/core/security.py`의
검증 로직(`get_current_profile_id`)은 전혀 안 바뀐다 — 로그인 방식이 바뀐 건 "누가
Supabase를 호출하느냐"뿐이고, 그 이후 토큰 검증 파이프라인은 이전 설계 그대로 재사용됨.

`SUPABASE_JWT_SECRET`을 아직 `.env`에 안 넣었다면 `get_current_profile_id`는 개발 편의상
`Authorization: Bearer <profile UUID>`를 그대로 프로필 id로 취급한다 (실제 검증 안 함).
데모 전에는 반드시 실제 Supabase 토큰 검증 경로로 바꿀 것.
