# FastAPI Backend Server

AI Hackathon을 위한 FastAPI 백엔드 서버입니다.

## 🚀 빠른 시작

### 필수 요구사항
- Python 3.11 이상
- pip

### 실행 방법

#### 1. 자동 설정 및 실행 (권장)

```bash
# 초기 설정 (최초 1회만)
./setup.sh

# 서버 시작
./start.sh
```

#### 2. 수동 설정 및 실행

```bash
# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정 (선택사항)
cp .env.example .env
# .env 파일을 필요에 따라 수정

# 서버 시작
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 서버 접속

서버가 시작되면 다음 URL로 접속할 수 있습니다:

- **API 문서 (Swagger UI)**: http://localhost:8000/docs
- **API 문서 (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📁 프로젝트 구조

```
.
├── app/
│   ├── __init__.py
│   └── main.py          # FastAPI 메인 애플리케이션
├── requirements.txt     # Python 의존성
├── .env.example         # 환경변수 예시
├── setup.sh            # 초기 설정 스크립트
├── start.sh            # 서버 시작 스크립트
└── README.md
```

## 🛠️ API 엔드포인트

### Health Check
- `GET /health` - 서버 상태 확인

### Example APIs
- `GET /` - 루트 엔드포인트
- `GET /api/hello?name=YourName` - 인사 API
- `POST /api/echo` - 에코 API

## 📚 API 문서

서버 실행 후 http://localhost:8000/docs 에서 자동 생성된 API 문서를 확인할 수 있습니다.

Swagger UI에서 다음 기능을 사용할 수 있습니다:
- 📖 모든 API 엔드포인트 확인
- 🧪 API 테스트 (Try it out)
- 📝 요청/응답 스키마 확인

## 🔧 개발

### 개발 모드

`--reload` 옵션으로 서버를 실행하면 코드 변경 시 자동으로 서버가 재시작됩니다.

```bash
uvicorn app.main:app --reload
```

### 새로운 API 추가

`app/main.py` 파일에 새로운 엔드포인트를 추가하면 됩니다:

```python
@app.get("/api/your-endpoint")
async def your_endpoint():
    return {"message": "Hello!"}
```

### 의존성 추가

새로운 Python 패키지가 필요한 경우:

```bash
# 가상환경 활성화 상태에서
pip install package-name

# requirements.txt 업데이트
pip freeze > requirements.txt
```

## 📝 환경변수

`.env.example` 파일을 참고하여 `.env` 파일을 생성하세요.

주요 환경변수:
- `ENV`: 환경 (development/production)
- `DEBUG`: 디버그 모드
- `ALLOWED_ORIGINS`: CORS 허용 오리진

## 🚀 배포

### 서버에 배포하기

1. **서버에 코드 복사**
```bash
git clone <repository-url>
cd AI-hackathon-AI
```

2. **초기 설정**
```bash
./setup.sh
```

3. **환경변수 설정**
```bash
cp .env.example .env
# .env 파일 수정 (production 설정)
```

4. **서버 시작**
```bash
# 개발 모드
./start.sh

# 프로덕션 모드 (백그라운드 실행)
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &
```

### systemd로 서비스 등록 (Linux)

`/etc/systemd/system/fastapi.service` 파일 생성:

```ini
[Unit]
Description=FastAPI Backend Service
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/AI-hackathon-AI
Environment="PATH=/path/to/AI-hackathon-AI/venv/bin"
ExecStart=/path/to/AI-hackathon-AI/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

서비스 시작:
```bash
sudo systemctl daemon-reload
sudo systemctl enable fastapi
sudo systemctl start fastapi
sudo systemctl status fastapi
```

## 🔍 문제 해결

### 포트가 이미 사용 중인 경우

```bash
# 8000 포트를 사용 중인 프로세스 확인
lsof -i :8000

# 프로세스 종료
kill -9 <PID>

# 또는 다른 포트 사용
uvicorn app.main:app --port 8080
```

### 가상환경 활성화가 안 되는 경우

```bash
# 가상환경 삭제 후 재생성
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 📄 라이선스

MIT License