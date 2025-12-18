
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


def normalize_plan_input(plan: Plan, candidates: List[Dict[str, Any]]) -> Plan:
    """
    사용자가 입력한 Brand/Category가 한글이거나 매핑되지 않는 경우,
    LLM을 통해 candidates에 존재하는 가장 적절한 영어 값으로 변환합니다.
    """
    if not candidates:
        return plan
        
    # 1. 가능한 브랜드 및 카테고리 수집
    known_brands = set()
    known_categories = set()
    for item in candidates:
        brand = item.get("brand")
        category = item.get("category")
        if brand:
            known_brands.add(brand)
        if category:
            known_categories.add(category)
            
    # 2. 이미 유효한지 체크 (둘 다 존재하면 패스)
    # 완전 일치를 위해 비교 (case-sensitive)
    if plan.brand in known_brands and plan.category in known_categories:
        return plan
        
    # 3. LLM을 통한 매핑
    # 리스트가 너무 길면 토큰 제한에 걸릴 수 있으므로, 적절히 자르거나 핵심만 전달
    brands_list = list(known_brands)
    categories_list = list(known_categories)
    
    system_prompt = f"""
    You are a data mapping assistant.
    Map the User's Input (Brand, Category) to the most semantic match from the Valid Lists.
    
    # Valid Lists
    - Brands: {brands_list}
    - Categories: {categories_list}
    
    # Core Rules
    1. If the input is Korean, translate and map it to the corresponding English term in Valid Lists.
    2. If the user swapped Brand and Category, correct them.
    3. If there is no exact match, choose the most relevant one.
    4. Return ONLY a JSON object with "brand" and "category".
    
    # Example
    Input: brand="영화", category="메가박스"
    Output: {{"brand": "Megabox", "category": "Movie"}}
    """
    
    user_input = f'brand="{plan.brand}", category="{plan.category}"'
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            response_format={"type": "json_object"},
            temperature=0
        )
        content = response.choices[0].message.content
        parsed = json.loads(content)
        
        # 매핑된 결과로 Plan 생성
        new_brand = parsed.get("brand", plan.brand)
        new_category = parsed.get("category", plan.category)
        
        print(f"[Normalization] {plan.brand}/{plan.category} -> {new_brand}/{new_category}")
        
        return Plan(
            dateTime=plan.datetime,
            brand=new_brand,
            category=new_category
        )
        
    except Exception as e:
        print(f"Plan normalization failed: {e}")
        return plan


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

    # 1. 입력 정규화 (한글 -> 영어 매핑)
    plan = normalize_plan_input(plan, offers + events)

    # 2. 문맥 최적화를 위한 1차 필터링 (Heuristic)
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
       - If 'cards_any_of' is present, AT LEAST ONE of user.payments MUST be in it.
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

    user_info = f"User(Telecom: {user.telecom}, Cards: {user.payments})"
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
        # benefit을 읽기 쉽게 포맷팅
        benefit_info = item.get("benefit")
        benefit_text = ""
        if benefit_info:
            kind = benefit_info.get("kind", "")
            value = benefit_info.get("value", 0)
            if kind == "percent":
                benefit_text = f"{value}% 할인"
            elif kind == "fixed":
                benefit_text = f"{int(value)}원 할인"
            elif kind == "cashback":
                # 100보다 크면 금액(원)으로 간주, 아니면 %(퍼센트)로 간주하는 휴리스틱 적용
                if value > 100:
                    benefit_text = f"{int(value)}원 캐시백"
                else:
                    benefit_text = f"{value}% 캐시백"
            elif kind == "points":
                benefit_text = f"{int(value)}P 적립"

        simplified_items.append({
            "id": item["id"],
            "brand": item.get("brand"),
            "title": item.get("title"),
            "benefit_text": benefit_text,  # 포맷팅된 혜택
            "benefit_raw": item.get("benefit"),  # 원본도 포함
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
    - **MANDATORY 1**: Use 'benefit_text' field to mention the EXACT benefit (e.g., "10% 할인", "5000원 할인"). If benefit_text is empty, use 'notes' or 'title'.
    - **MANDATORY 2**: Mention the schedule/time if relevant from 'constraints.times' (e.g., "10:30~20:00 이용 가능").
    - **MANDATORY 3**: If 'notes' exists, include key information from it (e.g., "최대 70% 할인 행사").
    - **MANDATORY 4**: Use 'reason_hint' as context but ALWAYS add specific benefit details.
    - Write in a friendly, polite tone (Korean, e.g., "~하세요", "~어때요?").
    - Keep it concise (1-2 sentences max).

    # Input Fields
    - benefit_text: Pre-formatted benefit in Korean (USE THIS FIRST!)
    - notes: Additional event/promotion details
    - reason_hint: Context about why this is an alternative
    - constraints.times: Time availability

    # Output Format
    JSON object with a key "descriptions" containing a list of objects:
    {"id": "item_id", "message": "생성된 추천 문장 (반드시 구체적 혜택 포함!)"}

    # Example
    Input: {"id": "o1", "brand": "Lotte", "benefit_text": "20% 할인", "reason_hint": "Shinsegae 대신 Lotte에서 혜택을 받아보세요"}
    Output: {"id": "o1", "message": "Shinsegae 대신 Lotte 백화점에서 20% 할인을 받아보세요"}
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
