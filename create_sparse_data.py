import json
import random
import os

# 파일 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

FULL_OFFERS_FILE = os.path.join(DATA_DIR, "offers.full.json")
FULL_EVENTS_FILE = os.path.join(DATA_DIR, "events.full.json")

SPARSE_OFFERS_FILE = os.path.join(DATA_DIR, "offers.sparse.json")
SPARSE_EVENTS_FILE = os.path.join(DATA_DIR, "events.sparse.json")

# 제거할 수 있는 필드 목록 (필수 필드인 id, type 등은 제외)
OPTIONAL_FIELDS = [
    "validity", 
    "benefit", 
    "eligibility", 
    "constraints", 
    "exclusions", 
    "source", 
    "notes",
    "channels"
]

def make_sparse(items, drop_rate=0.4):
    """
    아이템 리스트에서 무작위로 필드를 제거하여 결측치 데이터 생성
    :param items: 원본 아이템 리스트
    :param drop_rate: 필드 제거 확률 (0.0 ~ 1.0)
    """
    sparse_items = []
    
    for item in items:
        # 딥카피 대신 단순 복사 후 수정 (nested dict는 새로 생성됨)
        new_item = item.copy()
        
        # 각 옵션 필드에 대해 제거 여부 결정
        for field in OPTIONAL_FIELDS:
            if field in new_item and random.random() < drop_rate:
                # 필드 자체를 삭제하거나 None으로 설정
                # 여기서는 아예 키를 삭제하는 방식 사용
                del new_item[field]
                
        # nested 필드 내부의 부분 결측도 시뮬레이션 (예: validity의 end만 삭제)
        if "validity" in new_item and random.random() < 0.3:
            # start나 end 중 하나만 남기거나 둘 다 삭제
            val = new_item["validity"].copy()
            if random.random() < 0.5:
                if "start" in val: del val["start"]
            else:
                if "end" in val: del val["end"]
            new_item["validity"] = val

        if "eligibility" in new_item and random.random() < 0.3:
            elig = new_item["eligibility"].copy()
            if random.random() < 0.5 and "telecom_any_of" in elig:
                del elig["telecom_any_of"]
            if random.random() < 0.5 and "cards_any_of" in elig:
                del elig["cards_any_of"]
            new_item["eligibility"] = elig

        sparse_items.append(new_item)
        
    return sparse_items

def main():
    print("Creating sparse data...")
    
    # Offer 데이터 로드 및 변환
    if os.path.exists(FULL_OFFERS_FILE):
        with open(FULL_OFFERS_FILE, 'r', encoding='utf-8') as f:
            offers = json.load(f)
        
        sparse_offers = make_sparse(offers, drop_rate=0.3) # 30% 확률로 필드 제거
        
        with open(SPARSE_OFFERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(sparse_offers, f, ensure_ascii=False, indent=2)
            
        print(f"Created {SPARSE_OFFERS_FILE} ({len(sparse_offers)} items)")

    # Event 데이터 로드 및 변환
    if os.path.exists(FULL_EVENTS_FILE):
        with open(FULL_EVENTS_FILE, 'r', encoding='utf-8') as f:
            events = json.load(f)
            
        sparse_events = make_sparse(events, drop_rate=0.3)
        
        with open(SPARSE_EVENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(sparse_events, f, ensure_ascii=False, indent=2)
            
        print(f"Created {SPARSE_EVENTS_FILE} ({len(sparse_events)} items)")

    print("Done.")

if __name__ == "__main__":
    main()
