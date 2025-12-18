from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
import os
import json
from dotenv import load_dotenv
from pymongo import MongoClient

# .env 파일 로드
load_dotenv()

# MongoDB 연결 설정
MONGO_HOST = os.getenv("MONGO_HOST")
MONGO_PORT = int(os.getenv("MONGO_PORT")) if os.getenv("MONGO_PORT") else 27017
MONGO_USERNAME = os.getenv("MONGO_ROOT_USERNAME")
MONGO_PASSWORD = os.getenv("MONGO_ROOT_PASSWORD")
MONGO_DB = os.getenv("MONGO_DATABASE") or "jjdc"

# MongoDB 연결 시도
OFFERS = []
EVENTS = []
USE_MONGODB = False

if not MONGO_HOST or not MONGO_USERNAME or not MONGO_PASSWORD:
    print("MongoDB configuration missing, using JSON files")
    USE_MONGODB = False
else:
    try:
        client = MongoClient(
            host=MONGO_HOST,
            port=MONGO_PORT,
            username=MONGO_USERNAME,
            password=MONGO_PASSWORD,
            authSource="admin"
        )
        db = client[MONGO_DB]
        offers_collection = db["offers"]
        events_collection = db["events"]
        
        # MongoDB에서 데이터 로드
        OFFERS = list(offers_collection.find({}, {"_id": 0}))
        EVENTS = list(events_collection.find({}, {"_id": 0}))
        USE_MONGODB = True
        print(f"MongoDB connected: {MONGO_HOST}:{MONGO_PORT}")
        print(f"Loaded {len(OFFERS)} offers, {len(EVENTS)} events from MongoDB")
    except Exception as e:
        print(f"MongoDB connection failed: {e}")
        print("Loading from JSON files...")
        USE_MONGODB = False

# JSON 파일에서 fallback (MongoDB 미설정 또는 연결 실패 시)
if not USE_MONGODB:
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    OFFERS_FILE = os.path.join(DATA_DIR, "offers.full.json")
    EVENTS_FILE = os.path.join(DATA_DIR, "events.full.json")
    
    try:
        with open(OFFERS_FILE, 'r', encoding='utf-8') as f:
            OFFERS = json.load(f)
        with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
            EVENTS = json.load(f)
        print(f"Loaded {len(OFFERS)} offers, {len(EVENTS)} events from JSON files")
    except Exception as json_error:
        print(f"JSON file load failed: {json_error}")
        OFFERS = []
        EVENTS = []

# 모델 및 추천 로직 임포트
from app.models import (
    UserProfile, Plan, Offer, Event,
    RecommendationResponse, HealthCheckResponse
)
from app.recommender import recommend
from app.llm_recommender import get_ai_recommendations

# FastAPI 앱 생성
app = FastAPI(
    title="혜택 추천 API",
    description="AI Hackathon - 사용자 계획 기반 혜택/이벤트 추천 시스템",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS 설정
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 인메모리 데이터 저장
DATA_LOADED = False


# 앱 시작 이벤트
@app.on_event("startup")
async def startup_event():
    global DATA_LOADED
    DATA_LOADED = True
    print("FastAPI Backend Server Started")
    print(f"Loaded {len(OFFERS)} offers and {len(EVENTS)} events")
    print(f"Data source: {'MongoDB' if USE_MONGODB else 'JSON files'}")
    print("API Documentation: http://localhost:8000/docs")
    print("ReDoc Documentation: http://localhost:8000/redoc")


# 앱 종료 이벤트
@app.on_event("shutdown")
async def shutdown_event():
    print("FastAPI Backend Server Shutting Down")


# ============================================================================
# Health Check 엔드포인트
# ============================================================================

@app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check():
    """
    서버 상태 확인용 헬스체크 엔드포인트
    """
    return HealthCheckResponse(
        status="healthy",
        service="혜택 추천 API",
        version="1.0.0",
        data_loaded=DATA_LOADED,
        offers_count=len(OFFERS),
        events_count=len(EVENTS)
    )


# ============================================================================
# Root 엔드포인트
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """
    루트 엔드포인트 - API 정보 제공
    """
    return {
        "message": "혜택 추천 API에 오신 것을 환영합니다",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "recommend": "/api/recommend",
            "offers": "/api/offers",
            "events": "/api/events"
        },
        "data_stats": {
            "offers_count": len(OFFERS),
            "events_count": len(EVENTS)
        }
    }


# ============================================================================
# 데이터 조회 엔드포인트
# ============================================================================

@app.get("/api/offers", tags=["Data"])
async def get_offers(limit: int = 10, offset: int = 0):
    """
    Offer 목록 조회
    
    - **limit**: 반환할 최대 개수 (기본값: 10)
    - **offset**: 시작 위치 (기본값: 0)
    """
    total = len(OFFERS)
    items = OFFERS[offset:offset + limit]
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": items
    }


@app.get("/api/offers/{offer_id}", tags=["Data"])
async def get_offer(offer_id: str):
    """
    특정 Offer 조회
    
    - **offer_id**: Offer ID
    """
    for offer in OFFERS:
        if offer.get("id") == offer_id:
            return offer
    
    raise HTTPException(status_code=404, detail=f"Offer '{offer_id}' not found")


@app.get("/api/events", tags=["Data"])
async def get_events(limit: int = 10, offset: int = 0):
    """
    Event 목록 조회
    
    - **limit**: 반환할 최대 개수 (기본값: 10)
    - **offset**: 시작 위치 (기본값: 0)
    """
    total = len(EVENTS)
    items = EVENTS[offset:offset + limit]
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": items
    }


@app.get("/api/events/{event_id}", tags=["Data"])
async def get_event(event_id: str):
    """
    특정 Event 조회
    
    - **event_id**: Event ID
    """
    for event in EVENTS:
        if event.get("id") == event_id:
            return event
    
    raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found")


# ============================================================================
# 추천 엔드포인트
# ============================================================================

class RecommendRequest(BaseModel):
    """추천 요청"""
    user: UserProfile
    plan: Plan
    top_k: int = 5


@app.post("/api/recommend", response_model=RecommendationResponse, tags=["Recommendation"])
async def get_recommendations(request: RecommendRequest):
    """
    사용자 계획 기반 혜택/이벤트 추천 (Rule-based)
    
    - **user**: 사용자 프로필 (user_id, telecom, cards)
    - **plan**: 사용자 계획 (plan_id, user_id, datetime, brand, category)
    - **top_k**: 반환할 추천 개수 (기본값: 10)
    
    ## 추천 로직
    1. 유효기간 필터링 (validity)
    2. 자격 조건 필터링 (eligibility: telecom, cards)
    3. 점수 계산 (브랜드/카테고리 매칭, 혜택 가치 등)
    4. 상위 K개 반환
    """
    try:
        # 추천 실행
        recommendations = recommend(
            user=request.user,
            plan=request.plan,
            offers=OFFERS,
            events=EVENTS,
            top_k=request.top_k
        )
        
        return RecommendationResponse(
            plan_id=request.plan.plan_id,
            user_id=request.user.user_id,
            recommendations=recommendations,
            total_count=len(recommendations),
            timestamp=datetime.now().isoformat()
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"추천 처리 중 오류 발생: {str(e)}"
        )


@app.post("/api/recommend/ai", tags=["Recommendation"])
async def get_recommendations_ai(request: RecommendRequest):
    """
    [AI] 사용자 계획 기반 혜택/이벤트 추천 (OpenAI 기반)
    
    OpenAI API를 사용하여 맥락을 분석하고 추천합니다.
    응답 포맷이 변경되었습니다: {code, message, data: [{message, startAt, endAt}]}
    """
    if not os.environ.get("OPENAI_API_KEY"):
         return JSONResponse(
            status_code=501, 
            content={
                "code": 501,
                "message": "Server configuration error: OPENAI_API_KEY is not set.",
                "data": []
            }
        )

    try:
        # AI 추천 실행
        recommendations = get_ai_recommendations(
            user=request.user,
            plan=request.plan,
            offers=OFFERS,
            events=EVENTS
        )
        
        # Top K 필터링
        recommendations = recommendations[:request.top_k]
        
        # 포맷팅 (Standardized Response Format)
        formatted_data = []
        for item in recommendations:
            validity = item.get("validity", {}) or {}
            
            formatted_data.append({
                "message": item.get("ai_reason", item.get("title")), # ai_reason을 message로 사용
                "startAt": validity.get("start", ""),
                "endAt": validity.get("end", "")
            })

        return {
            "code": 200,
            "message": "성공",
            "data": formatted_data
        }
    
    except Exception as e:
        print(f"AI Recommendation failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "code": 500,
                "message": f"AI 추천 처리 중 오류 발생: {str(e)}",
                "data": []
            }
        )


@app.post("/api/recommend/alternatives", tags=["Recommendation"])
async def get_alternative_recommendations(request: RecommendRequest):
    """
    [대안 추천] 근처 시간대 혜택 및 동종 카테고리 대안 브랜드 추천
    
    Rule-based 추천 결과를 기반으로 LLM이 자연스러운 설명 문장을 생성하여 반환합니다.
    """
    try:
        from app.recommender import recommend_alternatives
        from app.llm_recommender import augment_with_llm_messages
        
        # 1. Rule-based 추천 (Top-3 씩만 추출하여 비용 절약)
        raw_result = recommend_alternatives(
            user=request.user,
            plan=request.plan,
            offers=OFFERS,
            events=EVENTS,
            top_k=3
        )
        
        # 2. 결과 병합 (Near Time + Category)
        # 우선순위: Near Time 먼저, 그 다음 Category
        candidates = raw_result.get("near_time_offers", []) + raw_result.get("category_alternatives", [])
        
        # 3. LLM을 이용한 문장 생성 및 포맷팅 (message, from, to)
        final_data = augment_with_llm_messages(candidates, request.plan)
        
        if not final_data:
             return {
                "code": 200,
                "message": "추천 가능한 대안이 없습니다.",
                "data": []
            }

        return {
            "code": 200,
            "message": "성공",
            "data": final_data
        }
    
    except Exception as e:
        # 에러 발생 시 지정된 포맷 반환
        return JSONResponse(
            status_code=500, 
            content={
                "code": 500,
                "message": f"에러: {str(e)}",
                "data": []
            }
        )


# ============================================================================
# 통계 엔드포인트
# ============================================================================

@app.get("/api/stats", tags=["Statistics"])
async def get_statistics():
    """
    데이터 통계 정보
    """
    # Offer 통계
    offers_with_validity = sum(1 for o in OFFERS if "validity" in o)
    offers_with_benefit = sum(1 for o in OFFERS if "benefit" in o)
    offers_with_eligibility = sum(1 for o in OFFERS if "eligibility" in o)
    
    offer_brands = set(o.get("brand") for o in OFFERS if o.get("brand"))
    offer_categories = set(o.get("category") for o in OFFERS if o.get("category"))
    
    # Event 통계
    events_with_validity = sum(1 for e in EVENTS if "validity" in e)
    events_with_notes = sum(1 for e in EVENTS if "notes" in e)
    events_with_eligibility = sum(1 for e in EVENTS if "eligibility" in e)
    
    event_brands = set(e.get("brand") for e in EVENTS if e.get("brand"))
    event_categories = set(e.get("category") for e in EVENTS if e.get("category"))
    
    return {
        "offers": {
            "total": len(OFFERS),
            "with_validity": offers_with_validity,
            "with_benefit": offers_with_benefit,
            "with_eligibility": offers_with_eligibility,
            "unique_brands": len(offer_brands),
            "unique_categories": len(offer_categories),
            "brands": sorted(list(offer_brands)),
            "categories": sorted(list(offer_categories))
        },
        "events": {
            "total": len(EVENTS),
            "with_validity": events_with_validity,
            "with_notes": events_with_notes,
            "with_eligibility": events_with_eligibility,
            "unique_brands": len(event_brands),
            "unique_categories": len(event_categories),
            "brands": sorted(list(event_brands)),
            "categories": sorted(list(event_categories))
        }
    }
