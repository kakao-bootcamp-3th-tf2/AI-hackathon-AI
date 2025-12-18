#!/bin/bash

# FastAPI 서버 시작 스크립트

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 FastAPI 백엔드 서버 시작...${NC}"

# venv 확인
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  가상환경이 없습니다. 가상환경을 생성합니다...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ 가상환경 생성 완료${NC}"
fi

# venv 활성화
echo -e "${BLUE}📦 가상환경 활성화...${NC}"
source venv/bin/activate

# 의존성 설치
echo -e "${BLUE}📚 의존성 설치 중...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo -e "${GREEN}✅ 의존성 설치 완료${NC}"

# 서버 시작
echo -e "${GREEN}🎉 서버를 시작합니다!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}📚 API 문서: http://localhost:8000/docs${NC}"
echo -e "${GREEN}📖 ReDoc: http://localhost:8000/redoc${NC}"
echo -e "${GREEN}💚 Health Check: http://localhost:8000/health${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
