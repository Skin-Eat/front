# Skin Basket

Skin Basket 해커톤 프로젝트 모노레포.

## 구조

```
lionideaton/          Android 프론트엔드 (git submodule -> heychaewong/lionideaton)
skinbasket-backend/    FastAPI 백엔드 (Supabase + Gemini + 네이버 검색 연동)
```

`lionideaton`은 서브모듈이라 별도 저장소(https://github.com/heychaewong/lionideaton)에서
관리된다. 클론 직후 프론트 코드까지 받으려면:

```bash
git clone --recurse-submodules https://github.com/Skin-Eat/front.git
# 이미 클론했다면:
git submodule update --init --recursive
```

백엔드 세부 사항은 `skinbasket-backend/README.md` 참고.
