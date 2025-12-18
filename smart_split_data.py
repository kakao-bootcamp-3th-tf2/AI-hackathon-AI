import json
import os
import copy
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OFFERS_FILE = os.path.join(DATA_DIR, "offers.full.json")
EVENTS_FILE = os.path.join(DATA_DIR, "events.full.json")

# 브랜드별 구체적 템플릿 (확실히 다른 혜택 부여)
TEMPLATES = {
    "Starbucks": {
        "telecom": [
            ("VIP 무료 사이즈업", {"kind": "fixed_amount", "value": 500, "min_spend": 4500, "max_benefit": 500}),
            ("아메리카노 Short 무료 (VIP)", {"kind": "free", "value": 4000, "min_spend": 0, "max_benefit": 4000})
        ],
        "card": [
            ("스타벅스 20% 청구할인", {"kind": "percent", "value": 20, "min_spend": 10000, "max_benefit": 5000}),
            ("5000원 이상 결제 시 1000원 캐시백", {"kind": "fixed_amount", "value": 1000, "min_spend": 5000, "max_benefit": 1000})
        ]
    },
    "GS25": {
        "telecom": [("멤버십 10% 할인 (최대 1000원)", {"kind": "percent", "value": 10, "min_spend": 1000, "max_benefit": 1000})],
        "card": [("행사상품 1+1 및 추가 10% 할인", {"kind": "percent", "value": 10, "min_spend": 5000, "max_benefit": 2000})]
    },
    "CU": {
        "telecom": [("VIP 도시락 무료 증정 쿠폰", {"kind": "free", "value": 4500, "min_spend": 0, "max_benefit": 4500})],
        "card": [("BC페이북 QR결제 시 500원 할인", {"kind": "fixed_amount", "value": 500, "min_spend": 3000, "max_benefit": 500})]
    },
    "CGV": {
        "telecom": [("영화 예매 무료 (연 6회)", {"kind": "free", "value": 15000, "min_spend": 0, "max_benefit": 15000})],
        "card": [("영화 3000원 청구할인", {"kind": "fixed_amount", "value": 3000, "min_spend": 10000, "max_benefit": 6000})]
    },
     "Shinsegae": {
        "telecom": [("통신사 VIP 음료쿠폰 2매", {"kind": "free", "value": 10000, "min_spend": 0, "max_benefit": 10000})],
        "card": [("제휴카드 5% 전자쿠폰 할인", {"kind": "percent", "value": 5, "min_spend": 50000, "max_benefit": 50000})]
    },
    "Coupang": {
        "telecom": [("멤버십 포인트 3000점 적립", {"kind": "fixed_amount", "value": 3000, "min_spend": 30000, "max_benefit": 3000})],
        "card": [("와우카드 4% 적립", {"kind": "percent", "value": 4, "min_spend": 10000, "max_benefit": 10000})]
    }
}

def mutate_benefit(benefit, mode):
    """
    템플릿이 없는 경우 랜덤하게 값을 변경하여 차별화
    """
    new_benefit = copy.deepcopy(benefit)
    val = new_benefit.get("value", 0)
    
    if mode == "telecom":
        # 통신사는 약 10% 낮게 설정 (보통 카드 혜택이 더 큼)
        factor = random.uniform(0.7, 0.9)
    else:
        # 카드는 조금 더 혜택을 크게
        factor = random.uniform(1.0, 1.3)
        
    if new_benefit.get("kind") == "percent":
        # 퍼센트는 5단위로 끊기
        new_val = int(val * factor / 5) * 5
        new_benefit["value"] = max(5, min(50, new_val)) # 5~50%
    else:
        # 금액은 100원 단위로 끊기
        new_val = int(val * factor / 100) * 100
        new_benefit["value"] = max(100, new_val)

    return new_benefit

def smart_split_and_vary(items):
    new_items = []
    
    for item in items:
        eligibility = item.get("eligibility", {})
        
        has_telecom = "telecom_any_of" in eligibility and eligibility["telecom_any_of"]
        has_cards = "cards_any_of" in eligibility and eligibility["cards_any_of"]
        
        # 둘 다 있으면 분리!
        if has_telecom and has_cards:
            brand = item.get("brand", "General")
            
            # --- 1. 통신사 혜택 ---
            t_item = copy.deepcopy(item)
            t_item["id"] = f"{item['id']}_telecom"
            del t_item["eligibility"]["cards_any_of"]
            
            if brand in TEMPLATES and "telecom" in TEMPLATES[brand]:
                title_suffix, benefit = random.choice(TEMPLATES[brand]["telecom"])
                t_item["title"] = f"{brand} {title_suffix}"
                t_item["benefit"] = benefit
            else:
                t_item["title"] = f"{item['title']} (통신사)"
                t_item["benefit"] = mutate_benefit(item.get("benefit", {}), "telecom")
            
            new_items.append(t_item)
            
            # --- 2. 카드사 혜택 ---
            c_item = copy.deepcopy(item)
            c_item["id"] = f"{item['id']}_card"
            del c_item["eligibility"]["telecom_any_of"]
            
            if brand in TEMPLATES and "card" in TEMPLATES[brand]:
                title_suffix, benefit = random.choice(TEMPLATES[brand]["card"])
                c_item["title"] = f"{brand} {title_suffix}"
                c_item["benefit"] = benefit
            else:
                c_item["title"] = f"{item['title']} (카드)"
                c_item["benefit"] = mutate_benefit(item.get("benefit", {}), "card")
                
            new_items.append(c_item)
            
        else:
            new_items.append(item)
            
    return new_items

def main():
    print("✨ Generating smart split (varied values)...")
    
    # Offer와 Event 모두 적용
    files = [OFFERS_FILE, EVENTS_FILE]
    
    for file_path in files:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            enriched_data = smart_split_and_vary(data)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(enriched_data, f, ensure_ascii=False, indent=2)
                
            print(f"✅ Processed {os.path.basename(file_path)}: {len(data)} -> {len(enriched_data)}")

if __name__ == "__main__":
    main()
