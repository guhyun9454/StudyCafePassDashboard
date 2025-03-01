import re
from datetime import datetime, time

# 1. 정가 상품 
normal_prices = {
    "정액시간권": {
        "50시간": {"price": [85000]},
        "100시간": {"price": [135000]},
    },
    "기간권": {
        "1주": {"price": [50000]},
        "2주": {"price": [90000]},
        "4주": {"price": [150000, 250000]},
        "8주": {"price": [2 * 150000, 2 * 250000]},
        "12주": {"price": [3 * 150000, 3 * 250000]},
        "20주": {"price": [5 * 150000, 5 * 250000]},
        "24주": {"price": [6 * 150000, 6 * 250000]},
        "28주": {"price": [7 * 150000, 7 * 250000]},
        "32주": {"price": [8 * 150000, 8 * 250000]},
        "36주": {"price": [9 * 150000, 9 * 250000]},
    }
}

# 2. 이벤트 상품
event_configs = {
    "241111오픈": {
        "이벤트기간": (datetime(2024, 11, 11), datetime(2024, 12, 31)),
        "정액시간권": {
            "100시간": {"이벤트상품": "110시간", "price": [135000]},
        },
        "기간권": {
            "4주": {"이벤트상품": "5주", "price": [150000, 250000]},
            "8주": {"이벤트상품": "10주", "price": [2 * 150000, 2 * 250000]},
        },
    },
    "250101새해": {
        "이벤트기간": (datetime(2025, 1, 1), datetime(2025, 1, 31)),
        "정액시간권": {
            "50시간": {"이벤트상품": "55시간", "price": [85000]},
            "100시간": {"이벤트상품": "110시간", "price": [135000]},
        },
        "기간권": {
            "2주": {"이벤트상품": "2주", "price": [90000]},
            "4주": {"이벤트상품": "5주", "price": [150000, 250000]},
            "8주": {"이벤트상품": "10주", "price": [2 * 150000, 2 * 250000]},
            "12주": {"이벤트상품": "15주", "price": [3 * 150000, 3 * 250000]},
            "20주": {"이벤트상품": "24주", "price": [5 * 150000, 5 * 250000]},
            "24주": {"이벤트상품": "30주", "price": [6 * 150000, 6 * 250000]},
            "28주": {"이벤트상품": "36주", "price": [7 * 150000, 7 * 250000]},
            "32주": {"이벤트상품": "42주", "price": [8 * 150000, 8 * 250000]},
            "36주": {"이벤트상품": "48주", "price": [9 * 150000, 9 * 250000]},
        },
    },
    "250224봄맞이": {
        "이벤트기간": (datetime(2025, 2, 24), datetime(2025, 3, 16)),
        "정액시간권": {
            "100시간": {"이벤트상품": "110시간", "price": [135000]},
        },
        "기간권": {
            "4주": {"이벤트상품": "5주", "price": [150000, 250000]},
        },
    },
}

def 기간권_parser(order_text):
    m = re.search(r"(\d{4}-\d{2}-\d{2})~(\d{4}-\d{2}-\d{2})", order_text)
    start_date = datetime.strptime(m.group(1), "%Y-%m-%d").date()
    end_date = datetime.strptime(m.group(2), "%Y-%m-%d").date()
    days = (end_date - start_date).days + 1
    weeks = days // 7
    actual = f"{weeks}주"
    return actual

def 정액시간권_parser(order_text):
    actual  = re.match(r"^(\d+시간)", order_text).group(1)
    return actual

def is_normal_product(row):
    order_text = row["주문명"].strip() #"2시간(2025-02-27~2025-02-27) 서비스 신청"
    category = row["구분"].strip() #정액시간권 or 기간권
    order_amount = int(str(row["합계금액"]).strip()) #85000

    found = False

    if category == "기간권":
        actual = 기간권_parser(order_text)

        for key, info in normal_prices["기간권"].items():
            if actual == key and order_amount in info["price"]:
                found = True
                break

    elif category == "정액시간권":
        actual  = 정액시간권_parser(order_text)
        
        for key, info in normal_prices["정액시간권"].items():
            if actual == key and order_amount in info["price"]:
                found = True
                break

    else:
        raise ValueError(f"Invalid category: {category}")

    return found

def is_event_product(event_name, row):
    order_text = row["주문명"].strip() #"2시간(2025-02-27~2025-02-27) 서비스 신청"
    category = row["구분"].strip() #정액시간권 or 기간권
    order_amount = int(str(row["합계금액"]).strip()) #85000

    if category == "정액시간권":
        actual  = 정액시간권_parser(order_text)

        for key, info in event_configs[event_name]["정액시간권"].items():
            if actual == info["이벤트상품"] and order_amount in info["price"]:
                return True
        return False

    elif category == "기간권":
        actual = 기간권_parser(order_text)
        for key, info in event_configs[event_name]["기간권"].items():
            if actual == info["이벤트상품"] and order_amount in info["price"]:
                return True
        return False

    else:
        raise ValueError(f"Invalid category: {category}")

def is_in_event_period(event_name, row):
    order_dt = row["주문일시"]
    start, end = event_configs[event_name]["이벤트기간"]
    end_full = datetime.combine(end.date(), time(23, 59, 59))
    return start <= order_dt <= end_full

def get_event_type(order_date):
    """
    주문일시(order_date)를 입력받아, event_configs에 정의된
    이벤트 기간(종료일은 23:59:59까지 포함)에 해당하면 이벤트 이름을 반환합니다.
    해당하는 이벤트가 없으면 None을 반환합니다.
    """
    for event, config in event_configs.items():
        start, end = config["이벤트기간"]
        event_end = datetime.combine(end.date(), time(23, 59, 59))
        if start <= order_date <= event_end:
            return event
    return None

# FIND 함수들 (과거/미래 이벤트와 거리(일수)를 함께 반환)
def find_closest_past_event(row):
    order_dt = row["주문일시"]
    closest_event = None
    closest_distance = None
    for event, config in event_configs.items():
        start, end = config["이벤트기간"]
        event_end = datetime.combine(end.date(), time(23, 59, 59))
        if event_end <= order_dt:
            diff = (order_dt - event_end).days
            if closest_distance is None or diff < closest_distance:
                closest_distance = diff
                closest_event = event
    return closest_event, closest_distance

def find_closest_future_event(row):
    order_dt = row["주문일시"]
    closest_event = None
    closest_distance = None
    for event, config in event_configs.items():
        start, end = config["이벤트기간"]
        if start >= order_dt:
            diff = (start - order_dt).days
            if closest_distance is None or diff < closest_distance:
                closest_distance = diff
                closest_event = event
    return closest_event, closest_distance

def calc_normal_sales_estimate(event_name, normal_df, overall_start_date, overall_end_date):
    """
    전체 데이터 기간 중, 이벤트 기간을 전부 제외한 날에 발생한 정가 매출 평균을 계산한 후,
    해당 이벤트 기간 일수만큼 곱하여 예상 정가 매출을 산출합니다.
    
    Parameters:
        event_name (str): 이벤트 이름 (예: "25새해")
        normal_df (DataFrame): 정가 매출 데이터 (정가 주문만 포함)
        overall_start_date (date): 전체 데이터 기간의 시작일
        overall_end_date (date): 전체 데이터 기간의 종료일
        
    Returns:
        float: 이벤트 기간 동안의 예상 정가 매출
    """
    # 이벤트 기간 가져오기
    if event_name not in event_configs:
        raise ValueError(f"알 수 없는 이벤트 이름: {event_name}")
    evt_start, evt_end = event_configs[event_name]["이벤트기간"]
    evt_start_date = evt_start.date()
    evt_end_date = evt_end.date()
    event_duration = (evt_end_date - evt_start_date).days + 1

    # 전체 데이터 기간의 일수 계산
    overall_duration = (overall_end_date - overall_start_date).days + 1

    # 전체 기간 중, 모든 이벤트 기간(중복 고려 없이)의 총 일수 계산
    total_event_days = 0
    for evt, config in event_configs.items():
        evt_s, evt_e = config["이벤트기간"]
        evt_s_date = evt_s.date()
        evt_e_date = evt_e.date()
        # 전체 기간과 해당 이벤트 기간의 교집합 일수 계산
        overlap_start = max(overall_start_date, evt_s_date)
        overlap_end = min(overall_end_date, evt_e_date)
        if overlap_start <= overlap_end:
            total_event_days += (overlap_end - overlap_start).days + 1

    # 이벤트 기간을 제외한 날 수
    non_event_days = overall_duration - total_event_days
    if non_event_days <= 0:
        return 0

    # 정가 매출 총합과 일일 평균 정가 매출 계산
    total_normal_sales = normal_df["합계금액"].sum()
    avg_normal_sales_per_day = total_normal_sales / non_event_days

    # 해당 이벤트 기간에 해당하는 예상 정가 매출 산출
    estimated_normal_sales = avg_normal_sales_per_day * event_duration

    return estimated_normal_sales , event_duration
