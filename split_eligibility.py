import json
import os
import copy

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OFFERS_FILE = os.path.join(DATA_DIR, "offers.full.json")
EVENTS_FILE = os.path.join(DATA_DIR, "events.full.json")

def split_items(items, item_type_name="item"):
    new_items = []
    split_count = 0
    
    for item in items:
        eligibility = item.get("eligibility", {})
        
        # 통신사와 카드 조건이 둘 다 있는지 확인
        has_telecom = "telecom_any_of" in eligibility and eligibility["telecom_any_of"]
        has_cards = "cards_any_of" in eligibility and eligibility["cards_any_of"]
        
        if has_telecom and has_cards:
            # 분리 작업 수행
            split_count += 1
            
            # 1. 통신사 혜택 생성
            item_telecom = copy.deepcopy(item)
            item_telecom["id"] = f"{item['id']}_telecom"
            # 제목에 (통신사) 추가 (중복 방지 체크)
            if "(통신사)" not in item_telecom["title"] and "(카드)" not in item_telecom["title"]:
                item_telecom["title"] = f"{item['title']} (통신사)"
            item_telecom["eligibility"] = {
                "telecom_any_of": eligibility["telecom_any_of"]
            }
            new_items.append(item_telecom)
            
            # 2. 카드사 혜택 생성
            item_card = copy.deepcopy(item)
            item_card["id"] = f"{item['id']}_card"
            if "(통신사)" not in item_card["title"] and "(카드)" not in item_card["title"]:
                item_card["title"] = f"{item['title']} (카드)"
            item_card["eligibility"] = {
                "cards_any_of": eligibility["cards_any_of"]
            }
            new_items.append(item_card)
            
        else:
            # 분리할 필요 없으면 그대로 유지
            new_items.append(item)
            
    return new_items, split_count

def main():
    print("Processing offers...")
    if os.path.exists(OFFERS_FILE):
        with open(OFFERS_FILE, 'r', encoding='utf-8') as f:
            offers = json.load(f)
        
        new_offers, o_splits = split_items(offers, "offer")
        
        with open(OFFERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_offers, f, ensure_ascii=False, indent=2)
        print(f"Offers: {len(offers)} -> {len(new_offers)} (Split {o_splits} items)")

    print("Processing events...")
    if os.path.exists(EVENTS_FILE):
        with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
            events = json.load(f)
            
        new_events, e_splits = split_items(events, "event")
        
        with open(EVENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_events, f, ensure_ascii=False, indent=2)
        print(f"Events: {len(events)} -> {len(new_events)} (Split {e_splits} items)")

    print("Done! Eligibility criteria have been split.")

if __name__ == "__main__":
    main()
