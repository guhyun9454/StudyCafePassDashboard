import re
from datetime import datetime, time
import pandas as pd
from event_utils import 정액시간권_parser, 기간권_parser, is_normal_product, get_event_type, is_event_product, find_closest_past_event, find_closest_future_event

def process_order_row(row):
    # 기본 값 추출
    category = row["구분"].strip()          # "정액시간권" or "기간권"
    
    if category not in ["정액시간권", "기간권"]:
        return pd.Series({
            "시간": None,
            "기간": None,
            "상품 유형": None,
            "이벤트명": None,
            "시작일": None,
            "종료일": None,
            "남은일수": None,
            "D-Day": None,
            "만료여부": None
        })
    
    order_text = row["주문명"].strip()
    order_dt = row["주문일시"]              
    order_amount = int(str(row["합계금액"]).strip())
    
    # 실제 이용시간/기간 파싱
    if category == "정액시간권":
        actual_usage = 정액시간권_parser(order_text)
        period_str = None
    elif category == "기간권":
        period_str = 기간권_parser(order_text)
        actual_usage = None
    else:
        actual_usage = None
        period_str = None

    # 1. 정가 여부 판단
    if is_normal_product(row):
        classification = "정가"
        event_name_out = None
        event_distance = None
    else:
        # 2. 이벤트 기간에 결제가 되었는가?
        current_event = get_event_type(order_dt)
        if current_event is not None:
            # 3. 그 이벤트인가?
            if is_event_product(current_event, row):
                classification = "이벤트"
                event_name_out = current_event
                event_distance = 0
            else:
                classification = "비정상"
                event_name_out = None
                event_distance = None
        else:
            # 4. 이벤트 기간에 결제되지 않은 경우: 두 FIND 함수를 사용
            past_event, past_dist = find_closest_past_event(row)
            future_event, future_dist = find_closest_future_event(row)
            if past_event is not None and future_event is not None:
                if past_dist <= future_dist:
                    chosen_event = past_event
                    chosen_distance = past_dist
                else:
                    chosen_event = future_event
                    chosen_distance = future_dist
                classification = "이벤트 의심"
                event_name_out = chosen_event
                event_distance = chosen_distance
            elif past_event is not None:
                classification = "이벤트 의심"
                event_name_out = past_event
                event_distance = past_dist
            elif future_event is not None:
                classification = "이벤트 의심"
                event_name_out = future_event
                event_distance = future_dist
            else:
                classification = "비정상"
                event_name_out = None
                event_distance = None

    # 기간권 추가 정보
    if category == "기간권":
        m = re.search(r"(\d{4}-\d{2}-\d{2})~(\d{4}-\d{2}-\d{2})", order_text)
        start_date_val = datetime.strptime(m.group(1), "%Y-%m-%d").date()
        end_date_val = datetime.strptime(m.group(2), "%Y-%m-%d").date()
        today = datetime.today().date()
        remaining_days = (end_date_val - today).days
        d_day_str = f"D-{remaining_days}" if remaining_days >= 0 else f"D+{abs(remaining_days)}"
        expired = end_date_val < today
    else:
        start_date_val = None
        end_date_val = None
        remaining_days = None
        d_day_str = None
        expired = None

    return pd.Series({
        "시간": actual_usage,
        "기간": period_str,
        "상품 유형": classification,
        "이벤트명": event_name_out,
        "시작일": start_date_val,
        "종료일": end_date_val,
        "남은일수": remaining_days,
        "D-Day": d_day_str,
        "만료여부": expired
    })