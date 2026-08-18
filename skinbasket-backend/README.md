# Skin Basket Backend (FastAPI + 가비아 MySQL + Supabase Auth)

**DB와 인증 제공자가 분리되어 있다**: 데이터는 가비아 DB호스팅(MySQL)에 저장하고,
로그인/회원가입(인증)만 계속 Supabase Auth를 쓴다. Supabase Auth의 JWT 검증은
stateless라 DB가 어디 있든 상관없이 동작하기 때문에 가능한 조합 — `profiles.id`가
Supabase가 발급한 JWT의 `sub`(UUID)와 같기만 하면 되고, Supabase의 실제 `auth.users`
테이블에 join하지 않는다. (이 조합 자체는 이번에 팀과 논의해서 정한 것 — 팀 전체
컨센서스인지 한 번 더 확인 권장.)

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
  services/   규칙 기반 점수 계산, OpenAI/네이버 API 클라이언트 — 로직 본체
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
| 인증 | Supabase Auth가 로그인/회원가입 자체를 처리한다고 가정(DB는 가비아를 써도 인증은 Supabase Auth 유지). 백엔드는 JWT만 검증하고 `profiles` 테이블(닉네임/피부타입/고민/제약)만 관리. **"프론트가 Supabase Auth SDK로 직접 로그인한다"는 세부 가정 자체는 여전히 팀 확인 필요** |
| 식사 기록 (`/meals`) | 등록 + 오늘/최근7일 조회 동작 |
| 분석 (`/analysis/deficiency`) | Android `SkinScoreCalculator.analyzeDeficiency`와 임계값 동일하게 이식, 최근 7일만, 저장 안 함 |
| 추천 (`/basket/recommendations`) | 부족 축 기반 주재료+보충옵션 반환 |
| 레시피 (`/recipes/{id}`, `POST /recipes/{id}/eat`) | eat는 폐쇄 루프의 핵심 — 레시피 재료명(`ingredients[].name`)을 food 테이블과 이름 매칭해 자동으로 식사 기록을 만듦 (매칭 방식은 추후 ID 매핑으로 교체 권장). `user_id`/`generated_by` 컬럼 추가함(AI 생성 레시피 저장용, 아직 저장 로직은 안 붙임). **recipe 15종 시드 데이터는 AI 담당자 SQL에 `cooking_time_minutes`/`servings`/`skin_benefits`가 없어서 아직 미반영 — 값 받으면 `scripts/seed.py`에 추가할 것** |
| 피부 기록 (`/skin-logs`) | 등록/조회 동작. 사진은 URL만 받음(Supabase Storage에 프론트가 직접 업로드한다는 전제) |
| 쇼핑 검색 | **백엔드에 없음.** 네이버 쇼핑검색 오픈API(`/v1/search/shop.json`)가 2026-07-31부로 완전 종료되고 공식 대체 API가 없음을 확인함. 쿠팡/컬리와 동일한 원칙(구매자용 쓰기 API 없음 → 프론트 딥링크)을 그대로 적용 — 프론트가 `https://msearch.shopping.naver.com/search/all?query=...` 같은 검색 결과 페이지를 여는 방식으로 처리 |
| AI 사진 인식 (`POST /ai/food-image`) | OpenAI(`gpt-4o-mini`, 비전) 호출, food 테이블에서 뽑은 후보 안에서만 고르게 프롬프트 강제. `OPENAI_API_KEY` 없으면 502 |
| AI 분석 코멘트 (`POST /ai/analysis-comment`) | **DRAFT.** 결핍 분석을 자연어 코멘트로 변환. 동작은 하지만 경로/응답 shape 미확정 — 프론트 확정 전까지 바뀔 수 있음 |
| AI 레시피 생성 (`POST /ai/recipe-suggestion`) | **DRAFT.** recipe 테이블 대신 부족 영양소/알레르기·비선호를 반영해 즉석 생성. 저장 여부·food 테이블 매칭 방식 미정 — `app/services/openai_client.py` docstring 참고 |
| 쿠팡/컬리/네이버쇼핑 연동 | 안 함 — 구매자용 쓰기 API가 없거나(쿠팡/컬리) 검색 API가 종료돼서(네이버) 셋 다 프론트가 딥링크 버튼으로 처리 |
| 점수 저장/캐싱 | 안 함 — 항상 조회 시점 계산 (공통 지침 확정 사항) |

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
- `DATABASE_URL`: 가비아 DB호스팅 콘솔에서 발급받은 접속 도메인/계정/DB명으로 채움
  (`mysql+pymysql://아이디:비밀번호@접속도메인:3306/DB이름`)
- `SUPABASE_URL`, `SUPABASE_JWT_SECRET`: **DB용이 아니라 인증(Auth) 전용.** Supabase 프로젝트 > Settings > API에서 확인
- `OPENAI_API_KEY`: 안 채우면 AI 기능만 502, 나머지는 정상 동작
- `APP_ENV`: 로컬은 기본값 `local` 그대로 두면 됨. 배포/데모 환경에서는 `production` 등으로
  바꿔야 `SUPABASE_JWT_SECRET` 미설정 시 인증이 뚫리는 개발용 폴백이 막힌다 (`app/core/security.py`).

## DB 마이그레이션

```bash
alembic revision --autogenerate -m "init"
alembic upgrade head
python scripts/seed.py     # 최소 시드 데이터 (food/ingredient)
```

가비아 콘솔/phpMyAdmin으로 테이블을 직접 만들 수도 있지만, 팀이 스키마를 계속 바꿀
예정이라 **alembic으로 버전 관리하는 걸 권장** — `models/*.py`만 고치고 autogenerate하면 됨.

## 실행

```bash
uvicorn app.main:app --reload --port 8000
```

- Swagger 문서: http://localhost:8000/docs
- 헬스체크: http://localhost:8000/health
- 안드로이드 에뮬레이터에서 접속 시 `NetworkModule.BASE_URL`이 이미 `http://10.0.2.2:8000/`로
  맞춰져 있음 — 포트를 8000 이외로 바꾸면 프론트에도 알릴 것.

## 인증 관련 확인 필요 사항 (팀 결정 필요)

DB는 가비아 MySQL, 인증은 Supabase Auth — 이 조합 자체가 팀 전체와 맞춘 것인지 먼저
확인할 것. 그 아래 세부 사항으로, `app/core/security.py`는 **"프론트가 Supabase Auth SDK로 직접 로그인하고, 발급받은
access token을 Authorization 헤더로 보낸다"**는 전제로 짜여 있다. 이게 맞다면 별도
`/login`, `/signup` 엔드포인트는 필요 없고 `/auth/profile`만 있으면 된다.
만약 팀이 자체 로그인 API(이메일/비밀번호를 백엔드가 직접 검증)를 원한다면
`security.py`의 인증 방식만 바꾸면 되고, 다른 라우터들의 `Depends(get_current_profile_id)`
시그니처는 그대로 재사용 가능 — 이 부분이 가장 먼저 팀과 맞춰야 할 결정사항이다.

`SUPABASE_JWT_SECRET`을 아직 `.env`에 안 넣었다면 `get_current_profile_id`는 개발 편의상
`Authorization: Bearer <profile UUID>`를 그대로 프로필 id로 취급한다 (실제 검증 안 함).
데모 전에는 반드시 실제 Supabase 토큰 검증 경로로 바꿀 것.
