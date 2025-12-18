from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os

# FastAPI 앱 생성
app = FastAPI(
    title="FastAPI Backend",
    description="AI Hackathon Backend API",
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


# Health Check 엔드포인트
@app.get("/health", tags=["Health"])
async def health_check():
    """
    서버 상태 확인용 헬스체크 엔드포인트
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "FastAPI Backend",
            "version": "1.0.0"
        }
    )


# Root 엔드포인트
@app.get("/", tags=["Root"])
async def root():
    """
    루트 엔드포인트 - API 정보 제공
    """
    return {
        "message": "Welcome to FastAPI Backend",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health"
    }


# 예시 API 엔드포인트
@app.get("/api/hello", tags=["Example"])
async def hello(name: str = "World"):
    """
    간단한 인사 API
    
    - **name**: 인사할 대상의 이름 (기본값: World)
    """
    return {
        "message": f"Hello, {name}!",
        "status": "success"
    }


@app.post("/api/echo", tags=["Example"])
async def echo(data: dict):
    """
    입력받은 데이터를 그대로 반환하는 에코 API
    
    - **data**: 반환할 JSON 데이터
    """
    return {
        "received": data,
        "status": "success"
    }


# 앱 시작 이벤트
@app.on_event("startup")
async def startup_event():
    print("🚀 FastAPI Backend Server Started!")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("📖 ReDoc Documentation: http://localhost:8000/redoc")


# 앱 종료 이벤트
@app.on_event("shutdown")
async def shutdown_event():
    print("👋 FastAPI Backend Server Shutting Down...")
