"""
추천 로직 (간단한 프로토타입)
- 결측치를 안전하게 처리
- UserProfile + Plan 기반으로 Offer/Event 필터링 및 점수화
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from app.models import UserProfile, Plan, Offer, Event


def safe_get(obj: Any, *keys: str, default: Any = None) -> Any:
    """중첩된 딕셔너리에서 안전하게 값 추출"""
    current = obj
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        elif hasattr(current, key):
            current = getattr(current, key, default)
        else:
            return default
        if current is None:
            return default
    return current


def is_valid_date(validity: Optional[Dict[str, Optional[str]]], target_date: str) -> bool:
    """유효기간 체크 (결측치 안전 처리)"""
    if not validity:
        return True  # validity 없으면 항상 유효
    
    start = validity.get("start")
    end = validity.get("end")
    
    try:
        target = datetime.fromisoformat(target_date.replace("Z", "+00:00"))
        
        if start:
            start_dt = datetime.fromisoformat(start)
            if target < start_dt:
                return False
        
        if end:
            end_dt = datetime.fromisoformat(end)
            if target > end_dt:
                return False
        
        return True
    except:
        return True  # 파싱 실패 시 유효한 것으로 간주


def check_eligibility(
    eligibility: Optional[Dict[str, Optional[List[str]]]],
    user_telecom: str,
    user_payments: List[str]
) -> bool:
    """자격 조건 체크 (결측치 안전 처리)"""
    if not eligibility:
        return True  # eligibility 없으면 모두 자격 있음

    telecom_list = eligibility.get("telecom_any_of")
    cards_list = eligibility.get("cards_any_of")

    # 둘 다 없으면 자격 있음
    if not telecom_list and not cards_list:
        return True

    # telecom 체크
    telecom_match = True
    if telecom_list:
        telecom_match = user_telecom in telecom_list

    # cards 체크 (payments로 변경됨)
    cards_match = True
    if cards_list:
        cards_match = any(card in cards_list for card in user_payments)

    # 둘 다 만족해야 함 (AND 조건)
    return telecom_match and cards_match


def calculate_score(
    item: Dict[str, Any],
    user: UserProfile,
    plan: Plan
) -> float:
    """추천 점수 계산 (0-100)"""
    score = 50.0  # 기본 점수
    
    # 브랜드 매칭 (+30점)
    item_brand = safe_get(item, "brand")
    if item_brand and item_brand == plan.brand:
        score += 30
    
    # 카테고리 매칭 (+20점)
    item_category = safe_get(item, "category")
    if item_category and item_category == plan.category:
        score += 20
    
    # Offer인 경우 benefit 가치 평가
    if item.get("type") == "offer":
        benefit = safe_get(item, "benefit")
        if benefit:
            kind = safe_get(benefit, "kind")
            value = safe_get(benefit, "value", default=0)
            
            if kind == "percent" and value:
                score += min(value / 2, 15)  # 최대 15점
            elif kind == "fixed" and value:
                score += min(value / 500, 10)  # 최대 10점
            elif kind == "cashback" and value:
                score += min(value / 2, 12)  # 최대 12점
            elif kind == "points" and value:
                score += min(value / 1000, 8)  # 최대 8점
    
    # Event인 경우 notes 존재 시 가산점
    if item.get("type") == "event":
        notes = safe_get(item, "notes")
        if notes:
            score += 5
    
    # channels에 "app" 포함 시 가산점
    channels = safe_get(item, "channels", default=[])
    if channels and "app" in channels:
        score += 5
    
    return min(score, 100)  # 최대 100점


def recommend(
    user: UserProfile,
    plan: Plan,
    offers: List[Dict[str, Any]],
    events: List[Dict[str, Any]],
    top_k: int = 10
) -> List[Dict[str, Any]]:
    """
    추천 로직
    1. 유효기간 필터링
    2. 자격 조건 필터링
    3. 점수 계산 및 정렬
    4. 상위 K개 반환
    """
    plan_datetime = plan.datetime
    
    # 모든 아이템 수집
    all_items = []
    
    # Offers 필터링
    for offer in offers:
        validity = safe_get(offer, "validity")
        eligibility = safe_get(offer, "eligibility")
        
        # 유효기간 체크
        if not is_valid_date(validity, plan_datetime):
            continue
        
        # 자격 조건 체크
        if not check_eligibility(eligibility, user.telecom, user.payments):
            continue
        
        # 점수 계산
        score = calculate_score(offer, user, plan)
        all_items.append({
            "item": offer,
            "score": score,
            "type": "offer"
        })
    
    # Events 필터링
    for event in events:
        validity = safe_get(event, "validity")
        eligibility = safe_get(event, "eligibility")
        
        # 유효기간 체크
        if not is_valid_date(validity, plan_datetime):
            continue
        
        # 자격 조건 체크
        if not check_eligibility(eligibility, user.telecom, user.payments):
            continue
        
        # 점수 계산
        score = calculate_score(event, user, plan)
        all_items.append({
            "item": event,
            "score": score,
            "type": "event"
        })
    
    # 점수 기준 정렬
    all_items.sort(key=lambda x: x["score"], reverse=True)
    
    # 상위 K개 반환 (점수 포함)
    top_items = all_items[:top_k]
    
    return [
        {
            **item["item"],
            "recommendation_score": round(item["score"], 2)
        }
        for item in top_items
    ]

from datetime import datetime, time

def is_time_in_range(target_datetime: str, start_time_str: str, end_time_str: str) -> bool:
    """시간이 범위 내에 있는지 확인"""
    if not start_time_str or not end_time_str:
        return True
        
    try:
        dt = datetime.fromisoformat(target_datetime)
        target_time = dt.time()
        
        start = datetime.strptime(start_time_str, "%H:%M").time()
        end = datetime.strptime(end_time_str, "%H:%M").time()
        
        # 자정을 넘기는 경우 (예: 23:00 ~ 02:00) 처리
        if start <= end:
            return start <= target_time <= end
        else:
            return start <= target_time or target_time <= end
            
    except Exception:
        return True


def recommend_alternatives(
    user: UserProfile,
    plan: Plan,
    offers: List[Dict[str, Any]],
    events: List[Dict[str, Any]],
    top_k: int = 5
) -> Dict[str, List[Dict[str, Any]]]:
    """
    대안 추천 로직
    1. Near Time: 브랜드/카테고리는 맞는데 시간이 안 맞거나, 시간 제약이 있는 혜택 중 현재 일정에 부합하는 것
    2. Category Alternative: 브랜드는 다르지만 같은 카테고리의 인기 혜택
    """
    
    near_time_candidates = []
    category_candidates = []
    
    # 통합 아이템 리스트
    items = []
    for o in offers:
        items.append({**o, "_type": "offer"})
    for e in events:
        items.append({**e, "_type": "event"})
        
    for item in items:
        # 공통 필터링: 유효기간, 자격조건
        if not is_valid_date(safe_get(item, "validity"), plan.datetime):
            continue
        if not check_eligibility(safe_get(item, "eligibility"), user.telecom, user.payments):
            continue
            
        score = calculate_score(item, user, plan)
        
        # 1. Near Time & Valid Time 로직
        # 브랜드가 일치하고 시간 제약(constraints.times)을 만족하는 경우 우선 추천
        if item.get("brand") == plan.brand:
            constraints = safe_get(item, "constraints")
            times = safe_get(constraints, "times")
            if times:
                start = times.get("start")
                end = times.get("end")
                # 시간이 범위 내에 있다면 "Near Time" (지금 바로 갈 수 있는) 추천으로 분류
                if is_time_in_range(plan.datetime, start, end):
                    item_copy = item.copy()
                    item_copy["alternative_reason"] = f"{plan.brand} 방문 예정 시간에 이용 가능합니다 ({start}~{end})"
                    item_copy["score"] = score + 20 # 가산점
                    near_time_candidates.append(item_copy)
            else:
                # 시간 제약이 없는 경우도 Near Time 후보로 포함 (항상 이용 가능하므로)
                item_copy = item.copy()
                item_copy["alternative_reason"] = f"{plan.brand} 언제든지 이용 가능합니다"
                item_copy["score"] = score + 10
                near_time_candidates.append(item_copy)

        # 2. Category Alternative 로직
        # 브랜드는 다르지만 카테고리가 같은 경우
        if item.get("brand") != plan.brand and item.get("category") == plan.category:
            item_copy = item.copy()
            item_copy["alternative_reason"] = f"{plan.brand} 대신 {item.get('brand')}에서 혜택을 받아보세요"
            
            # 다른 브랜드라도 평점이 높거나 혜택이 좋으면 추천
            # 기본 score에는 브랜드 점수가 빠져있으므로 약간의 보정은 필요할 수 있음
            item_copy["score"] = score 
            category_candidates.append(item_copy)

    # 정렬 및 Top-K
    near_time_candidates.sort(key=lambda x: x["score"], reverse=True)
    category_candidates.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "near_time_offers": near_time_candidates[:top_k],
        "category_alternatives": category_candidates[:top_k]
    }
