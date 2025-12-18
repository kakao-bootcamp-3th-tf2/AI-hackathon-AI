import json
import random
import os
from datetime import datetime, timedelta

# 파일 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OFFERS_FILE = os.path.join(BASE_DIR, "data", "offers.full.json")
EVENTS_FILE = os.path.join(BASE_DIR, "data", "events.full.json")

# 랜덤 데이터 풀
TELECOMS = ["SKT", "KT", "LGU+"]
CARDS = ["ShinhanCheck", "KB_NaraSarang", "HyundaiCard", "SamsungCard", "LotteCard", "WooriCard", "HanaCard", "CitiCard"]
PREFIXES = ["[주말특가]", "[깜짝혜택]", "[마감임박]", "[평일한정]", "[멤버십]", "[단독]", "[New]"]

def random_date(start_str, end_str):
    """주어진 범위 내의 랜덤 날짜 반환"""
    start = datetime.strptime(start_str, "%Y-%m-%d")
    end = datetime.strptime(end_str, "%Y-%m-%d")
    delta = end - start
    random_days = random.randint(0, delta.days)
    return (start + timedelta(days=random_days)).strftime("%Y-%m-%d")

def generate_validity():
    """2025년 12월 ~ 2026년 2월 사이 랜덤 기간 생성"""
    start_base = datetime(2025, 12, 1)
    end_base = datetime(2026, 2, 28)
    
    start_date = start_base + timedelta(days=random.randint(0, 60))
    duration = random.randint(7, 30)
    end_date = start_date + timedelta(days=duration)
    
    return {
        "start": start_date.strftime("%Y-%m-%d"),
        "end": end_date.strftime("%Y-%m-%d")
    }

def enrich_items(items, item_type="offer"):
    enriched = []
    
    for item in items:
        # 원본 유지
        enriched.append(item)
        
        # 1~2개의 변형 데이터 생성
        num_copies = random.randint(1, 2)
        
        for i in range(num_copies):
            new_item = item.copy()
            
            # ID 변경
            new_item["id"] = f"{item['id']}_copy_{i+1}"
            
            # 제목 변경
            prefix = random.choice(PREFIXES)
            if prefix not in new_item["title"]:
                new_item["title"] = f"{prefix} {new_item['title']}"
            
            # 유효기간 약간 변경
            new_item["validity"] = generate_validity()
            
            # 자격조건(Eligibility) 랜덤 변경
            new_item["eligibility"] = {
                "telecom_any_of": random.sample(TELECOMS, k=random.randint(1, 3)),
                "cards_any_of": random.sample(CARDS, k=random.randint(1, 4))
            }
            
            # 혜택(Offer) 수치 약간 변경
            if item_type == "offer" and "benefit" in new_item:
                benefit = new_item["benefit"].copy()
                if benefit["kind"] == "percent":
                    benefit["value"] = min(90, max(5, benefit["value"] + random.choice([-5, 0, 5])))
                elif benefit["kind"] in ["fixed", "points", "cashback"]:
                    benefit["value"] = max(100, benefit["value"] + random.choice([-1000, -500, 500, 1000]))
                new_item["benefit"] = benefit
                
            # Offer 제약조건(Constraints) 요일 변경
            if item_type == "offer" and "constraints" in new_item:
                constraints = new_item["constraints"].copy()
                days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
                constraints["days_of_week"] = random.sample(days, k=random.randint(2, 7))
                new_item["constraints"] = constraints

            enriched.append(new_item)
            
    return enriched

def main():
    print("Loading data...")
    with open(OFFERS_FILE, 'r', encoding='utf-8') as f:
        offers = json.load(f)
    
    with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
        events = json.load(f)
        
    print(f"Original Offers: {len(offers)}")
    print(f"Original Events: {len(events)}")
    
    # 데이터 증식
    enriched_offers = enrich_items(offers, "offer")
    enriched_events = enrich_items(events, "event")
    
    # 셔플 (순서 섞기)
    random.shuffle(enriched_offers)
    random.shuffle(enriched_events)
    
    print(f"Enriched Offers: {len(enriched_offers)}")
    print(f"Enriched Events: {len(enriched_events)}")
    
    # 저장
    with open(OFFERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(enriched_offers, f, ensure_ascii=False, indent=2)
        
    with open(EVENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(enriched_events, f, ensure_ascii=False, indent=2)
        
    print("Data enrichment complete! Files updated.")

if __name__ == "__main__":
    main()
