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
- **JSON 기반 데이터**: `data/offers.full.json`, `data/events.full.json` 파일로 관리 (서버 재시작 시 자동 로드)
- **100% Full Data**: 결측치 없는 고품질 더미 데이터 (Offer 60여개, Event 30여개)
- **풍부한 메타데이터**: 유효기간, 요일/시간 제약, 통신사/카드 자격요건 등 상세 포함

---

## 🛠️ 설치 및 실행

### 1. 필수 요구사항
- Python 3.11 이상
- OpenAI API Key (AI 추천 기능 사용 시)

### 2. 자동 설정 및 실행 (권장)

```bash
# 초기 설정 (가상환경 생성, 패키지 설치)
./setup.sh

# 환경변수 설정 (최초 1회)
cp .env.example .env
# .env 파일을 열어 OPENAI_API_KEY를 입력하세요!

# 서버 시작
./start.sh
```

### 3. 수동 실행

```bash
source venv/bin/activate
pip install -r requirements.txt
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
    "user": {"user_id": "u1", "telecom": "SKT", "cards": ["ShinhanCheck"]},
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
├── requirements.txt         # 의존성 패키지 목록
└── .env                     # 환경변수 (API Key 등)
```

## 🔍 환경변수 설정 (.env)

`.env.example`을 복사하여 `.env`를 만들고 설정하세요.

```ini
OPENAI_API_KEY=sk-your-api-key-here  # AI 추천 기능을 위해 필수
DEBUG=True
ALLOWED_ORIGINS=http://localhost:3000
```

## 📄 라이선스
MIT License