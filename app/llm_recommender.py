import os
import json
from typing import List, Dict, Any
from openai import OpenAI
from app.models import UserProfile, Plan

# OpenAI 클라이언트 초기화 (API 키는 환경변수에서 로드)
# 주의: API 키가 없으면 에러가 발생할 수 있으므로 try-except 처리
try:
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
except Exception as e:
    print(f"Warning: OpenAI Client initialization failed: {e}")
    client = None

def get_ai_recommendations(
    user: UserProfile,
    plan: Plan,
    offers: List[Dict[str, Any]],
    events: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    OpenAI API를 사용하여 사용자 계획에 맞는 혜택 추천
    """
    if not client or not os.environ.get("OPENAI_API_KEY"):
        raise Exception("OpenAI API Key is missing. Please check .env file.")

    # 1. 문맥 최적화를 위한 1차 필터링 (Heuristic)
    # 브랜드나 카테고리가 일치하는 항목만 LLM에게 전달하여 토큰 절약
    candidates = []
    
    for item in offers + events:
        # 브랜드 일치 (가장 중요)
        if item.get("brand") == plan.brand:
            candidates.append(item)
            continue
            
        # 카테고리 일치
        if item.get("category") == plan.category:
            candidates.append(item)
            continue
            
        # TODO: "전가맹점" 등 범용 혜택이 있다면 여기서 포함
    
    # 후보가 너무 많으면 상위 N개로 제한 (예: 20개)
    candidates = candidates[:20]
    
    if not candidates:
        return []

    # 2. 프롬프트 구성
    system_prompt = """
    You are a helpful AI assistant that recommends the best benefits (offers/events) for a user's specific plan.
    
    # Input Data
    1. User Profile: Telecom, Cards
    2. User Plan: Brand, Category, Date
    3. Candidate Benefits: List of available offers and events
    
    # Task
    Analyze the candidates and select the ones that are valid and beneficial for the user's plan.
    
    # Rules
    1. Check 'validity': The plan date must be within [start, end].
    2. Check 'eligibility': 
       - If 'telecom_any_of' is present, user.telecom MUST be in it.
       - If 'cards_any_of' is present, AT LEAST ONE of user.cards MUST be in it.
    3. Check 'constraints':
       - Check 'days_of_week' (plan date is 2025-12-18 which is Thursday).
    4. Prioritize benefits that match the Brand exactly.
    
    # Output Format
    Return a valid JSON object with a key "recommendations".
    "recommendations" should be a list of objects, each containing:
    - "id": The ID of the benefit
    - "reason": A short explanation in Korean why this is recommended
    - "score": A relevance score (0-100)
    
    Example:
    {
        "recommendations": [
            {"id": "offer_001", "reason": "스타벅스 브랜드가 일치하고 SKT 통신사 할인이 적용됩니다.", "score": 95}
        ]
    }
    """

    user_info = f"User(Telecom: {user.telecom}, Cards: {user.cards})"
    plan_info = f"Plan(Brand: {plan.brand}, Category: {plan.category}, Date: {plan.datetime})"
    
    # 간소화된 후보 리스트 (토큰 절약을 위해 일부 필드만 보냄)
    candidates_simplified = []
    for c in candidates:
        candidates_simplified.append({
            "id": c.get("id"),
            "title": c.get("title"),
            "brand": c.get("brand"),
            "validity": c.get("validity"),
            "eligibility": c.get("eligibility"),
            "constraints": c.get("constraints"),
            "benefit": c.get("benefit")
        })

    user_message = f"""
    [User Profile]
    {user_info}
    
    [User Plan]
    {plan_info}
    
    [Candidates]
    {json.dumps(candidates_simplified, ensure_ascii=False)}
    """

    # 3. LLM 호출
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # 비용 효율적인 모델 사용 (또는 gpt-4o)
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        content = response.choices[0].message.content
        result = json.loads(content)
        
        # 4. 결과 매핑
        # LLM이 반환한 ID를 기반으로 원본 데이터 찾기
        final_recommendations = []
        rec_map = {r["id"]: r for r in result.get("recommendations", [])}
        
        for item in candidates:
            if item["id"] in rec_map:
                rec_info = rec_map[item["id"]]
                item_copy = item.copy()
                item_copy["recommendation_score"] = rec_info["score"]
                item_copy["ai_reason"] = rec_info["reason"]
                final_recommendations.append(item_copy)
        
        # 점수순 정렬
        final_recommendations.sort(key=lambda x: x.get("recommendation_score", 0), reverse=True)
        
        return final_recommendations

    except Exception as e:
        print(f"Error during OpenAI API call: {e}")
        return []
