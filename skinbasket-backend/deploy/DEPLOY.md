# 배포 체크리스트 (가비아 g클라우드)

이 문서에 있는 콘솔 조작/도메인 연결/SSH 접속은 여기서 대신 실행할 수 없는 작업이라
직접 진행해야 한다. `deploy/skinbasket-backend.service`, `deploy/nginx.conf.template`은
그 과정에서 그대로 복사해 쓸 파일.

## 0. 전제

- 배포 구조: Vercel(프론트) → 가비아(이 문서 — FastAPI 백엔드 호스팅) → Supabase(DB+Auth).
  DB는 가비아가 아니라 **Supabase Postgres**에 있다 — 가비아는 이 앱을 실행만 한다.
- DB는 이미 Supabase 프로젝트에 떠 있고 `.env`의 `DATABASE_URL`이 로컬에서 검증됐다고 가정.
  (아직이면 이 문서보다 로컬 `alembic upgrade head` + `python scripts/seed.py`가 먼저.)
- 이 배포는 "가비아 클라우드(g클라우드)" — 가상서버(VM) 상품이다. 앱만 여기서 돌리고
  DB 접속은 그 VM에서 인터넷 너머 Supabase로 나간다.
- **도메인 없이 IP로만 테스트하는 경우** (지금 이 상황): 4번(nginx+HTTPS) 단계는
  통째로 건너뛰어도 된다. 안드로이드 매니페스트에 `usesCleartextTraffic="true"`가 이미
  전역으로 켜져 있어서 평문 HTTP도 추가 설정 없이 붙는다. 그 대신 2번에서 80/443이
  아니라 **8000번 포트**를 열어야 하고, 최종 주소는 `http://VM의공인IP:8000`이 된다.
  나중에 도메인이 생기면 그때 4번부터 이어서 하면 됨.

## 1. VM 준비

1. 가비아 클라우드 콘솔에서 g클라우드 서버 생성 (Ubuntu 22.04 LTS 권장, 최소 사양이면 충분 — 해커톤 트래픽 규모)
2. 방화벽(보안 그룹)에서 인바운드 허용: **SSH(22)는 항상. IP만으로 테스트할 거면 8000번도 추가**
   (나중에 도메인+HTTPS로 갈 때는 80/443을 열고 8000은 닫아도 됨 — nginx가 8000을 대신 가려줌)
3. SSH 접속 후 기본 패키지 설치 (IP만 테스트할 거면 nginx/certbot은 지금 안 깔아도 됨):
   ```bash
   sudo apt update
   sudo apt install -y python3-venv python3-pip git
   # 나중에 도메인+HTTPS로 갈 때 추가 설치: sudo apt install -y nginx certbot python3-certbot-nginx
   ```
4. 배포 전용 유저 생성 (root로 직접 돌리지 않기 위함):
   ```bash
   sudo useradd -m -s /bin/bash skinbasket
   sudo su - skinbasket
   ```

## 2. 코드 배포

```bash
git clone https://github.com/Skin-Eat/front.git
cd front/skinbasket-backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env   # DATABASE_URL(Supabase Postgres), SUPABASE_URL/SUPABASE_JWT_SECRET, OPENAI_API_KEY,
            # APP_ENV=production 채우기
```

**`APP_ENV=production`으로 바꾸는 걸 잊지 말 것** — `local`로 두면 `SUPABASE_JWT_SECRET`이
비어 있을 때 인증이 뚫리는 개발용 폴백이 배포 환경에서도 그대로 켜진다 (`app/core/security.py`).

```bash
alembic upgrade head
python scripts/seed.py
deactivate
```

## 3. systemd로 상시 구동

```bash
exit   # skinbasket 유저에서 나와서 sudo 권한 있는 계정으로
sudo cp /home/skinbasket/front/skinbasket-backend/deploy/skinbasket-backend.service /etc/systemd/system/
# 유닛 파일 안의 경로가 실제 clone 위치(.../front/skinbasket-backend)와 다르면 맞춰서 수정
```

**IP만으로 테스트할 거면** 복사한 `/etc/systemd/system/skinbasket-backend.service`를 열어서
`ExecStart` 줄의 `--host 127.0.0.1`을 **`--host 0.0.0.0`**으로 바꿀 것 (`sudo nano ...`) —
안 바꾸면 서버 안에서만 접속되고 밖에서는 안 열린다. nginx를 앞에 두는 정식 배포로 갈 때는
다시 `127.0.0.1`로 되돌리고 nginx가 8000을 대신 가리게 할 것.

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now skinbasket-backend
sudo systemctl status skinbasket-backend   # active (running) 확인
```

## 4. nginx + HTTPS

도메인이 있어야 certbot으로 인증서를 받을 수 있다 (가비아에서 도메인 구매했거나 이미
있는 도메인의 서브도메인을 이 서버 IP로 A 레코드 연결).

```bash
sudo cp /home/skinbasket/front/skinbasket-backend/deploy/nginx.conf.template /etc/nginx/sites-available/skinbasket-backend
sudo sed -i 's/YOUR_DOMAIN/실제도메인/' /etc/nginx/sites-available/skinbasket-backend
sudo ln -s /etc/nginx/sites-available/skinbasket-backend /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d 실제도메인
```

도메인이 아직 없다면 이 4번 단계는 건너뛰고 3번까지만 하면 된다 (위 "0. 전제"의
IP-only 경로 참고) — `AndroidManifest.xml`에 `usesCleartextTraffic="true"`가 이미
전역으로 켜져 있어서 평문 HTTP도 별도 예외 설정 없이 붙는다. 다만 이건 테스트/데모용
편의고, 실제 배포는 도메인+HTTPS 권장.

## 5. 검증

```bash
curl https://실제도메인/health        # 도메인+HTTPS로 갔을 때
curl http://VM의공인IP:8000/health   # IP만으로 테스트할 때
```
로컬이 아니라 **외부에서** (핸드폰 데이터망 등, VM과 같은 네트워크 말고) 위 요청과 `/docs`
접속이 되는지 확인할 것 — 방화벽/보안그룹에서 막혀 있으면 서버 안에서는 되는데 밖에서는
안 되는 경우가 흔하다.

## 6. 프론트에 전달할 것

- `https://실제도메인` (또는 IP만 쓰는 경우 `http://VM의공인IP:8000`) — 안드로이드
  `NetworkModule.BASE_URL`을 이걸로 교체
- Supabase 프로젝트 URL + **anon(공개) 키** — 프론트가 Supabase Auth SDK로 로그인할 때 필요.
  (`SUPABASE_JWT_SECRET`, `OPENAI_API_KEY`, `DATABASE_URL`은 서버 `.env`에만
  두고 절대 앱/프론트 저장소에 넣지 말 것 — 앱은 디컴파일되면 그 안의 문자열이 그대로 노출된다.)

## 7. 배포 후 갱신할 때

```bash
sudo su - skinbasket
cd front/skinbasket-backend
git pull
source .venv/bin/activate
pip install -r requirements.txt   # 의존성 바뀌었을 때만
alembic upgrade head              # 마이그레이션 추가됐을 때만
deactivate
exit
sudo systemctl restart skinbasket-backend
```
