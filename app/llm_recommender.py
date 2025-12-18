
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
    5. **CRITICAL**: You MUST mention the specific benefit details (e.g., "20% discount", "5000 won off", "1+1 event") in the 'reason'.
    6. **CRITICAL**: When explaining conditions, mention ONLY the condition that matches. 
       - If the benefit is for Telecom only, mention ONLY the Telecom. 
       - If it's for Card only, mention ONLY the matched Card.
       - DO NOT say "SKT and Shinhan are applied" if the benefit is only for SKT.
    7. **CRITICAL**: If the item is an EVENT or has a vague title (e.g., "Festival", "Promotion"), you MUST use the details from the 'notes' field to explain what the benefit is (e.g., "Up to 70% off", "Free gifts").
    
    # Output Format
    Return a valid JSON object with a key "recommendations".
    "recommendations" should be a list of objects, each containing:
    - "id": The ID of the benefit
    - "reason": A detailed explanation in Korean. STRICTLY follow Rule #6 and #7.
    - "score": A relevance score (0-100)
    
    Example:
    {
        "recommendations": [
            {"id": "offer_001_telecom", "reason": "스타벅스에서 20% 할인을 받을 수 있으며, SKT 멤버십이 적용됩니다.", "score": 95}
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

    # 3. LLM 호출 및 파싱
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        content = response.choices[0].message.content
        parsed = json.loads(content)
        
        # 결과 매핑
        recommendations = []
        rec_map = {item["id"]: item for item in parsed.get("recommendations", [])}
        
        for item in candidates:
            if item["id"] in rec_map:
                rec_info = rec_map[item["id"]]
                item_copy = item.copy()
                item_copy["recommendation_score"] = rec_info.get("score", 0)
                item_copy["ai_reason"] = rec_info.get("reason", "")
                recommendations.append(item_copy)
                
        # 점수순 정렬
        recommendations.sort(key=lambda x: x["recommendation_score"], reverse=True)
        return recommendations
        
    except Exception as e:
        print(f"Error LLM recommendation: {e}")
        return candidates[:5]


def augment_with_llm_messages(items: List[Dict[str, Any]], plan: Plan) -> List[Dict[str, Any]]:
    """
    아이템 리스트를 받아 LLM을 이용해 'message' (추천 설명)를 생성하여 추가함 (자연스러운 한국어 문장)
    """
    if not items:
        return []
        
    # 1. 입력 줄이기 (비용/속도 최적화)
    simplified_items = []
    for item in items:
        simplified_items.append({
            "id": item["id"],
            "brand": item.get("brand"),
            "title": item.get("title"),
            "benefit": item.get("benefit"),
            "notes": item.get("notes"),
            "validity": item.get("validity"),  # 기간 정보 추가
            "constraints": item.get("constraints"), # 시간 정보 추가
            "reason_hint": item.get("alternative_reason", "")
        })
        
    user_plan_str = f"Plan: {plan.brand} ({plan.category}) at {plan.datetime}"
    
    system_prompt = """
    You are an AI assistant. Your task is to generate a natural and friendly Korean recommendation sentence for each item provided.
    
    # Context
    The user originally planned: {user_plan}
    However, we are recommending these alternative benefits.
    
    # Task
    For each item in the input list, generate a 'message' field.
    - Explain WHY this is a good alternative.
    - **MANDATORY 1**: Mention specific benefit details (e.g., "20% Discount", "1000 Won Cashback", "Free Size-up").
    - **MANDATORY 2**: Mention the schedule/time if relevant (e.g., "until Jan 5th", "10 AM to 8 PM", "on Weekends").
    - **MANDATORY 3**: Mention ONLY the condition (Card or Telecom) that is actually required for this item. Do NOT list all user's cards if not relevant.
    - **MANDATORY 4**: For Events/Festivals, explicitly mention what the event offers based on 'notes' (e.g., "Up to 70% sale").
    - Write in a friendly, polite tone (Korean, e.g., "~해요", "~어때요?").
    - Keep it concise (1-2 sentences).
    
    # Output Format
    JSON object with a key "descriptions" containing a list of objects:
    {"id": "item_id", "message": "생성된 추천 문장 (혜택, 일정, 정확한 조건, 상세 내용 포함)"}
    """
    
    desc_map = {}
    
    # LLM 호출
    if client and os.environ.get("OPENAI_API_KEY"):
         try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt.replace("{user_plan}", user_plan_str)},
                    {"role": "user", "content": json.dumps(simplified_items, ensure_ascii=False)}
                ],
                temperature=0.5
            )
            content = response.choices[0].message.content
            parsed = json.loads(content)
            desc_map = {d["id"]: d["message"] for d in parsed.get("descriptions", [])}
         except Exception as e:
            print(f"LLM generation failed: {e}")
    
    # 2. 결과 병합 및 포맷팅 (requested format: message, from, to)
    result_data = []
    for item in items:
        validity = item.get("validity", {}) or {}
        start_date = validity.get("start", "")
        end_date = validity.get("end", "")
        
        # LLM 메시지 없으면 기본 reason 사용
        message = desc_map.get(item["id"], item.get("alternative_reason", item.get("title", "")))
        
        result_data.append({
            "message": message,
            "startAt": start_date,
            "endAt": end_date
            # id 등 다른 정보는 제거 (요청 포맷 준수)
        })
        
    return result_data
