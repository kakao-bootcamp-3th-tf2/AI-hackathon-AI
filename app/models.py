"""
혜택 추천 API 데이터 모델 (Pydantic)
- UserProfile, Plan, Offer, Event 모델 정의
- Optional 필드를 명시적으로 처리
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ============================================================================
# 입력 데이터 모델 (고정)
# ============================================================================

class UserProfile(BaseModel):
    """사용자 프로필 (필드 추가 금지)"""
    telecom: str
    payments: List[str]


class Plan(BaseModel):
    """사용자 계획 (필드 추가 금지)"""
    datetime: str = Field(alias='dateTime')  # ISO 8601 format
    brand: str
    category: str

    class Config:
        populate_by_name = True  # datetime과 dateTime 둘 다 허용


# ============================================================================
# Offer/Event 서브 모델
# ============================================================================

class Validity(BaseModel):
    """유효기간"""
    start: Optional[str] = None
    end: Optional[str] = None


class Benefit(BaseModel):
    """혜택 정보"""
    kind: Optional[str] = None  # percent|fixed|cashback|points|unknown
    value: Optional[float] = None
    min_spend: Optional[float] = None
    max_benefit: Optional[float] = None


class Eligibility(BaseModel):
    """자격 조건"""
    telecom_any_of: Optional[List[str]] = None
    cards_any_of: Optional[List[str]] = None


class TimeRange(BaseModel):
    """시간 범위"""
    start: Optional[str] = None  # HH:MM
    end: Optional[str] = None    # HH:MM


class UsageLimit(BaseModel):
    """사용 제한"""
    period: Optional[str] = None  # daily|weekly|monthly
    count: Optional[int] = None


class Constraints(BaseModel):
    """제약 조건"""
    days_of_week: Optional[List[int]] = None  # 0-6
    times: Optional[TimeRange] = None
    usage_limit: Optional[UsageLimit] = None
    exclusive_group: Optional[str] = None


class Source(BaseModel):
    """출처 정보"""
    url: Optional[str] = None
    provider: Optional[str] = None


# ============================================================================
# Offer/Event 메인 모델
# ============================================================================

class Offer(BaseModel):
    """혜택 (Offer)"""
    id: str  # 필수
    type: str = "offer"
    title: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    validity: Optional[Validity] = None
    benefit: Optional[Benefit] = None
    channels: Optional[List[str]] = None
    eligibility: Optional[Eligibility] = None
    constraints: Optional[Constraints] = None
    exclusions: Optional[List[str]] = None
    source: Optional[Source] = None


class Event(BaseModel):
    """이벤트 (Event)"""
    id: str  # 필수
    type: str = "event"
    title: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    validity: Optional[Validity] = None
    channels: Optional[List[str]] = None
    eligibility: Optional[Eligibility] = None
    notes: Optional[str] = None
    source: Optional[Source] = None


# ============================================================================
# 응답 모델
# ============================================================================

class RecommendationResponse(BaseModel):
    """추천 결과 응답"""
    plan_id: str
    user_id: str
    recommendations: List[Dict[str, Any]]  # Offer 또는 Event
    total_count: int
    timestamp: str


class HealthCheckResponse(BaseModel):
    """헬스체크 응답"""
    status: str
    service: str
    version: str
    data_loaded: bool
    offers_count: int
    events_count: int
