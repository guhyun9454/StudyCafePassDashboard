import re
from datetime import datetime, time
import pandas as pd

# 1. 정가(일반 상품) 정의
normal_products = {
    "50시간": {"duration": "50시간", "price": 85000},
    "100시간": {"duration": "100시간", "price": 135000},
    "4주": {"duration": "4주", "price": [150000, 250000]},  # 4주권 정가 (15만원, 25만원 모두 포함)
    "2주": {"duration": "2주", "price": 90000},
    "1주": {"duration": "1주", "price": 50000},
}

# 2. 이벤트 조건을 동일 포맷으로 정의 
event_configs = {
    "24오픈": { 
        "period": (datetime(2024, 11, 11), datetime(2024, 12, 31)),
        "adjustments": {
            "100시간": {"bonus": "10시간", "expected": "110시간", "price_same": True},
            "4주": {"bonus": "1주", "expected": "5주", "price_same": True},
        },
    },
    "25새해": { 
        "period": (datetime(2025, 1, 1), datetime(2025, 1, 31)),
        "adjustments": {
            "50시간": {"bonus": "5시간", "expected": "55시간", "price_same": True},
            "100시간": {"bonus": "10시간", "expected": "110시간", "price_same": True},
            "2주": {"bonus": "3일", "expected": "2주+3일", "price_same": True},
            "4주": {"bonus": "1주", "expected": "5주", "price_same": True},
            "8주": {"bonus": "2주", "expected": "10주", "price_same": True},
            "12주": {"bonus": "3주", "expected": "15주", "price_same": True},
            "20주": {"bonus": "4주", "expected": "24주", "price_same": True},
            "24주": {"bonus": "6주", "expected": "30주", "price_same": True},
            "28주": {"bonus": "8주", "expected": "36주", "price_same": True},
            "32주": {"bonus": "10주", "expected": "42주", "price_same": True},
            "36주": {"bonus": "12주", "expected": "48주", "price_same": True},
        },
    },
    "25봄맞이": { 
        "period": (datetime(2025, 2, 24), datetime(2025, 3, 16)),
        "adjustments": {
            "100시간": {"bonus": "10시간", "expected": "110시간", "price_same": True},
            "4주": {"bonus": "1주", "expected": "5주", "price_same": True},
        },
    },
}

def get_event_type(order_date):
    """주문일시(order_date)를 기준으로 해당 이벤트 타입(open, new_year, spring)을 반환."""
    for event, config in event_configs.items():
        start, end = config["period"]
        end =  datetime.combine(end.date(), time(23, 59, 59))

        if start <= order_date <= end:
            return event
    return None

def process_order_row_extended(row):
    """주문 데이터를 처리하여 이벤트, 정가, 비정상 여부를 판별하고 필요한 정보를 반환한다."""
    order_type = row["구분"].strip() if row["구분"] else ""
    주문명 = row["주문명"].strip() if row["주문명"] else ""

    actual_usage = None
    period_str = None
    classification = None  # "정가", "이벤트", "이벤트 의심", "비정상"
    event_name = None
    start_date_val = None
    end_date_val = None
    remaining_days = None
    d_day_str = None
    expired = None

    # 주문일시는 미리 to_datetime 처리되어 있음.
    order_dt = row["주문일시"]
    event_type = get_event_type(order_dt) if order_dt else None

    # 합계금액 처리: 정가 상품 판별 (4주권은 15만원, 25만원 모두 포함)
    try:
        order_amount = int(str(row["합계금액"]).strip())
    except Exception:
        order_amount = None
    base_product = None
    for prod, info in normal_products.items():
        if isinstance(info["price"], list):  # 가격이 여러 개일 경우 (예: 4주권)
            if order_amount in info["price"]:
                base_product = prod
                break
        else:
            if order_amount == info["price"]:
                base_product = prod
                break

    # 분류 로직
    if order_type == "정액시간권":
        m = re.match(r"^(\d+시간)", 주문명)
        if m:
            actual_usage = m.group(1)
        if event_type:  # 주문일시가 이벤트 기간 내이면 이벤트로 분류
            classification = "이벤트"
            event_name = event_type
        else:
            if base_product:
                normal_duration = normal_products[base_product]["duration"]
                event_expected = None
                for ev, cfg in event_configs.items():
                    if base_product in cfg["adjustments"]:
                        candidate = cfg["adjustments"][base_product]["expected"]
                        if actual_usage == candidate:
                            event_expected = candidate
                            break
                if actual_usage == normal_duration:
                    classification = "정가"
                elif event_expected is not None:
                    classification = "이벤트 의심"
                else:
                    classification = "비정상"
            else:
                classification = "비정상"
    
    elif order_type == "기간권":
        m = re.search(r"(\d{4}-\d{2}-\d{2})~(\d{4}-\d{2}-\d{2})", 주문명)
        if m:
            try:
                start_date_val = datetime.strptime(m.group(1), "%Y-%m-%d").date()
                end_date_val = datetime.strptime(m.group(2), "%Y-%m-%d").date()
                days = (end_date_val - start_date_val).days + 1
                weeks = days // 7
                period_str = f"{weeks}주"
            except Exception:
                period_str = None
        else:
            period_str = None

        today = datetime.today().date()
        if end_date_val:
            remaining_days = (end_date_val - today).days
            d_day_str = f"D-{remaining_days}" if remaining_days >= 0 else f"D+{abs(remaining_days)}"
            expired = end_date_val < today
        else:
            remaining_days = None
            d_day_str = None
            expired = None

        if event_type:
            classification = "이벤트"
            event_name = event_type
        else:
            if base_product:
                normal_duration = normal_products[base_product]["duration"]
                event_expected = None
                for ev, cfg in event_configs.items():
                    if base_product in cfg["adjustments"]:
                        candidate = cfg["adjustments"][base_product]["expected"]
                        if period_str == candidate:
                            event_expected = candidate
                            break
                if period_str == normal_duration:
                    classification = "정가"
                elif event_expected is not None:
                    classification = "이벤트 의심"
                else:
                    classification = "비정상"
            else:
                classification = "비정상"

    else:
        classification = None

    # 이벤트가 아니면 event_name을 None으로 설정
    if classification != "이벤트":
        event_name = None

    return pd.Series({
        "실제 이용시간": actual_usage,
        "기간": period_str,
        "상품 유형": classification,
        "이벤트명": event_name,
        "시작일": start_date_val,
        "종료일": end_date_val,
        "남은일수": remaining_days,
        "D-Day": d_day_str,
        "만료여부": expired
    })
