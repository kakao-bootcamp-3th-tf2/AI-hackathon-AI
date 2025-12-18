#!/bin/bash

# FastAPI 프로젝트 초기 설정 스크립트

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 FastAPI 프로젝트 초기 설정...${NC}"

# Python 버전 확인
echo -e "${BLUE}🐍 Python 버전 확인...${NC}"
python3 --version

# 가상환경 생성
echo -e "${BLUE}📦 가상환경 생성 중...${NC}"
python3 -m venv venv
echo -e "${GREEN}✅ 가상환경 생성 완료${NC}"

# 가상환경 활성화
echo -e "${BLUE}🔌 가상환경 활성화...${NC}"
source venv/bin/activate

# pip 업그레이드
echo -e "${BLUE}⬆️  pip 업그레이드...${NC}"
pip install --upgrade pip

# 의존성 설치
echo -e "${BLUE}📚 의존성 설치 중...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}✅ 의존성 설치 완료${NC}"

# 환경변수 파일 생성
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚙️  .env 파일 생성...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✅ .env 파일 생성 완료 (필요시 수정하세요)${NC}"
else
    echo -e "${YELLOW}⚠️  .env 파일이 이미 존재합니다.${NC}"
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✨ 설정이 완료되었습니다!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}서버를 시작하려면:${NC}"
echo -e "  ${YELLOW}./start.sh${NC}"
echo ""
echo -e "${BLUE}또는 수동으로:${NC}"
echo -e "  ${YELLOW}source venv/bin/activate${NC}"
echo -e "  ${YELLOW}uvicorn app.main:app --reload${NC}"
echo ""
