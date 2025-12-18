# 혜택 추천 API (AI Hackathon Backend)

사용자의 프로필(통신사, 카드)과 계획(브랜드, 카테고리, 일정)을 분석하여 최적의 혜택을 추천해주는 FastAPI 백엔드 서비스입니다.
Rule-based 필터링뿐만 아니라 **OpenAI를 활용한 문맥 기반 추천**과 **시간/카테고리 기반 대안 추천** 기능을 제공합니다.

## 🚀 주요 기능

### 1. 혜택 추천 (3가지 모드)
| 모드 | 엔드포인트 | 설명 |
|------|-----------|------|
| **기본 추천** | `/api/recommend` | 유효기간, 자격조건, 점수 기반의 Rule-based 추천 |
| **AI 추천** | `/api/recommend/ai` | **OpenAI GPT**를 활용하여 문맥을 파악하고 추천 사유를 생성 |
| **대안 추천** | `/api/recommend/alternatives` | 시간대가 맞지 않거나 혜택이 없을 때, **인근 시간대**나 **경쟁 브랜드** 혜택 제안 |

### 2. 데이터 관리
- **MongoDB**: Docker 환경에서 MongoDB 컨테이너로 데이터 관리 (권장)
- **JSON 파일**: `data/offers.full.json`, `data/events.full.json` 파일로 관리 (MongoDB 미사용 시 fallback)
- **자동 전환**: MongoDB 연결 실패 시 자동으로 JSON 파일에서 로드

---

## 🛠️ 설치 및 실행

### 1. 필수 요구사항
- Python 3.10
- Docker & Docker Compose (Docker 실행 시)
- OpenAI API Key (AI 추천 기능 사용 시)

### 2. Docker로 실행 (권장)

```bash
# 환경변수 설정
cp .env.example .env
# .env 파일을 열어 필요한 값들을 입력하세요

# AI 서버 실행
docker compose -f docker-compose.ai.yaml up -d

# MongoDB 실행
docker compose -f docker-compose.mongo.yaml up -d

# 로그 확인
docker compose -f docker-compose.ai.yaml logs -f
```

### 3. 로컬 개발 환경

```bash
# 가상환경 생성 및 활성화
python3.10 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일을 열어 필요한 값들을 입력하세요

# 서버 실행
uvicorn app.main:app --reload
```

---

## 📚 API 사용 가이드

서버가 실행되면 **Swagger UI** (http://localhost:8000/docs) 에서 모든 API를 즉시 테스트할 수 있습니다.

### 1. 기본 추천 요청 (`POST /api/recommend`)
가장 빠르고 기본적인 추천입니다.

```bash
curl -X POST http://localhost:8000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "user": {"telecom": "SKT", "payments": ["ShinhanCheck"]},
    "plan": {"brand": "Starbucks", "category": "Cafe", "datetime": "2025-12-18T14:00:00"}
  }'
```

### 2. AI 추천 요청 (`POST /api/recommend/ai`)
OpenAI가 분석한 **추천 사유(`ai_reason`)**를 함께 받아볼 수 있습니다.

```bash
curl -X POST http://localhost:8000/api/recommend/ai \
  -H "Content-Type: application/json" \
  -d @test_request.json
```

### 3. 대안 추천 요청 (`POST /api/recommend/alternatives`)
원하는 브랜드의 혜택이 없거나 조건이 맞지 않을 때 유용합니다.
- **Near Time**: "지금은 안 되지만 1시간 뒤면 쓸 수 있는 쿠폰"
- **Category Alternative**: "스타벅스 쿠폰은 없지만 이디야 쿠폰은 있어요"

---

## 📁 프로젝트 구조

```
.
├── app/
│   ├── main.py              # FastAPI 메인 (엔드포인트 정의)
│   ├── models.py            # Pydantic 데이터 모델
│   ├── recommender.py       # Rule-based & 대안 추천 로직
│   └── llm_recommender.py   # OpenAI 기반 추천 로직
├── data/                    # 데이터 저장소
│   ├── offers.full.json     # Offer 데이터 (JSON)
│   └── events.full.json     # Event 데이터 (JSON)
├── docker-compose.ai.yaml   # AI 서버 Docker Compose 설정
├── docker-compose.mongo.yaml # MongoDB Docker Compose 설정
├── Dockerfile               # Docker 이미지 빌드 설정
├── requirements.txt         # 의존성 패키지 목록
├── .env.example             # 환경변수 예시 파일
└── .env                     # 환경변수 (실제 값, Git에 커밋하지 않음)
```

## 🔍 환경변수 설정 (.env)

`.env.example`을 복사하여 `.env`를 만들고 실제 값들을 입력하세요.

```ini
# AI / OpenAI
OPENAI_API_KEY=input-your-openai-api-key
ALLOWED_ORIGINS=https://jjdc.marcuth.store,http://localhost:3000,http://localhost:8000

# MongoDB
MONGO_HOST=jjdc-mongo
MONGO_PORT=27017
MONGO_ROOT_USERNAME=input-mongodb-username
MONGO_ROOT_PASSWORD=input-mongodb-password
MONGO_DATABASE=jjdc

# Docker Image (CI/CD에서 사용)
DOCKER_IMAGE_NAME_AI=ktb-jjdc-ai
```

---

## 🗄️ MongoDB 사용법 (Docker 환경)

### MongoDB 컨테이너 접속
```bash
docker exec -it jjdc-mongo mongosh -u input-mongodb-username -p input-mongodb-password --authenticationDatabase admin
```

### JSON 파일 Import
```bash
# offers 데이터 삽입
docker exec -i jjdc-mongo mongosh -u input-mongodb-username -p input-mongodb-password \
  --authenticationDatabase admin jjdc \
  --eval "db.offers.insertMany($(cat data/offers.full.json))"

# events 데이터 삽입
docker exec -i jjdc-mongo mongosh -u input-mongodb-username -p input-mongodb-password \
  --authenticationDatabase admin jjdc \
  --eval "db.events.insertMany($(cat data/events.full.json))"
```

### 데이터 조회
```bash
# 컬렉션 목록
docker exec -it jjdc-mongo mongosh -u input-mongodb-username -p input-mongodb-password \
  --authenticationDatabase admin --eval "use jjdc; show collections"

# offers 조회
docker exec -it jjdc-mongo mongosh -u input-mongodb-username -p input-mongodb-password \
  --authenticationDatabase admin --eval "use jjdc; db.offers.find().limit(5)"

# events 조회
docker exec -it jjdc-mongo mongosh -u input-mongodb-username -p input-mongodb-password \
  --authenticationDatabase admin --eval "use jjdc; db.events.find().limit(5)"
```

### Python 코드에서 접근 (pymongo)
```python
from pymongo import MongoClient
import os

client = MongoClient(
    host=os.getenv("MONGO_HOST", "jjdc-mongo"),
    port=int(os.getenv("MONGO_PORT", "27017")),
    username=os.getenv("MONGO_ROOT_USERNAME"),
    password=os.getenv("MONGO_ROOT_PASSWORD"),
    authSource="admin"
)
db = client[os.getenv("MONGO_DATABASE", "jjdc")]
offers = db["offers"]
events = db["events"]

# 조회
offer = offers.find_one({"brand": "Starbucks"})

# 삽입
offers.insert_one({"id": "o1", "title": "테스트"})
```

---

## 📄 라이선스
MIT License
