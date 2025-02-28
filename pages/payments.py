import streamlit as st
import pandas as pd
import altair as alt
from streamlit_timeline import st_timeline
import re
from datetime import datetime

from events import process_order_row
from utils import categorize_dday, init_page
init_page("💳 결제 로그 분석")



if "df" not in st.session_state:
    st.warning("🚨 먼저 홈에서 파일을 업로드해주세요.")
    st.stop()

# 🔄 **초기화 & 업로드 페이지로 이동하는 버튼**
if st.sidebar.button("🔄 다시 업로드하기"):
    st.session_state.clear()  # 세션 초기화
    st.rerun()  # 업로드 페이지로 이동

# 📌 사이드바에서 페이지 선택
st.sidebar.title("📌 메뉴")
page = st.sidebar.radio(
    "이동할 페이지를 선택하세요",
    ["📈 매출", "📅 기간권", "📅 사물함", "🏆 회원별 결제 금액","test"]
)


df = st.session_state["df"]

# 날짜 변환
df["주문일시"] = pd.to_datetime(df["주문일시"], errors="coerce")

# 📌 "결제완료" 상태의 주문만 필터링
df_paid = df[(df["주문상태"] == "결제완료") & (df["이름"] != "관리자")]

# 📌 데이터의 첫 주문일시 & 마지막 주문일시 감지
min_date = df["주문일시"].min().date() if not df["주문일시"].isna().all() else None
max_date = df["주문일시"].max().date() if not df["주문일시"].isna().all() else None

# 📌 데이터 기간 + 현재 날짜 기준 필터링 안내 추가
if min_date and max_date:
    st.info(f"📆 **이 데이터는 {min_date}부터 {max_date}까지의 결제 내역입니다. 기간 내의 데이터만 집계됩니다.** ")

# 📌 주문명에서 날짜 추출 함수
def extract_dates(order_name):
    match = re.search(r"(\d{4}-\d{2}-\d{2})[^\d]+(\d{4}-\d{2}-\d{2})", order_name)
    if match:
        return match.group(1), match.group(2)
    return None, None

# 📅 이용 내역 페이지 (기간권 / 사물함)
if page in ["📅 기간권", "📅 사물함"]:
    title_map = {
        "📅 기간권": "기간권",
        "📅 사물함": "사물함",
    }
    st.title(f"📅 {title_map[page]} 이용 내역")
    st.caption("💡 타임라인 속 각 항목을 클릭하면 왼쪽에서 상세한 결제 정보를 확인할 수 있습니다.")
    # 📅 현재 날짜
    today = datetime.today().date()

    # ✅ "같은 사람 한 줄에 보기" 활성화 여부 확인
    st.sidebar.subheader("📌 타임라인 옵션")
    group_by_user = st.sidebar.checkbox("같은 사람 한 줄에 보기", value=True)
    show_expired = st.sidebar.checkbox("만료된 기간권 보기", value=False)
    st.sidebar.divider()
    search_name = st.sidebar.text_input("🔍 회원 검색 (이름 입력)", "")


    # 📌 타임라인 데이터 생성 (만료된 데이터 선택적으로 제외)
    timeline_df = df_paid[df_paid["구분"] == title_map[page]].copy()

    # 📌 🔍 검색어가 입력되면 해당 이름이 포함된 데이터만 필터링
    if search_name:
        timeline_df = timeline_df[timeline_df["이름"].str.contains(search_name, case=False, na=False)]

    timeline_events = []

    # 📌 D-Day 데이터 저장
    dday_counts = {}  # D-Day별 인원수 저장
    future_count = 0   # D-Day가 0 이상인 회원 수
    valid_users = set()  # ✅ 실제 타임라인 이벤트가 있는 사용자만 저장

    for _, row in timeline_df.iterrows():
        start_date, end_date = extract_dates(row["주문명"])

        if start_date and end_date:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()

            # ✅ 기간권 주 수 계산
            weeks = ((end_date_obj - start_date_obj).days + 1) // 7

            # ✅ D-Day 계산
            d_day_value = (end_date_obj - today).days
            d_day = f"D+{abs(d_day_value)}" if d_day_value < 0 else f"D-{d_day_value}"

            # ✅ D-Day가 0 이상인 회원 수 카운트
            if d_day_value >= 0:
                future_count += 1
                # ✅ D-Day별 인원수 저장
                if d_day_value not in dday_counts:
                    dday_counts[d_day_value] = 0
                dday_counts[d_day_value] += 1

            # ✅ 만료된 기간권 필터링
            if show_expired or end_date_obj >= today:
                event = {
                    "id": int(row["No"]),
                    "name": row["이름"],
                    "content": f"{row['이름']}: {weeks}주 ({d_day})",  
                    "start": start_date,
                    "end": end_date,
                    "d_day_value": d_day_value,
                    "weeks" : weeks,
                    "style": "background-color: pink; color: black; border-color: red" if end_date_obj < today else ""
                }
                timeline_events.append(event)
                valid_users.add(row["이름"])  # ✅ 실제 표시할 데이터가 있는 사용자만 그룹으로 포함

    # ✅ 빈 그룹 문제 해결: 유효한 사용자만 그룹으로 포함
    if group_by_user and valid_users:
        groups = [{"id": idx, "content": name} for idx, name in enumerate(valid_users)]
        user_id_map = {g["content"]: g["id"] for g in groups}  # ✅ 사용자 이름 → ID 매핑

        for event in timeline_events:
            event["group"] = user_id_map[event["name"]]  # ✅ 그룹 ID 적용
    else:
        groups = []

    # 📌 D-Day가 0 이상인 회원 수 표시
    st.metric("기간 남은 회원 수", f"{future_count} 명")

    # 📌 타임라인 표시
    if timeline_events:
        timeline = st_timeline(timeline_events, groups=groups if group_by_user else [], options={'orientation':'top'}, height="600px")

        # 선택된 ID를 기반으로 데이터 출력
        if timeline:
            selected_id = timeline["id"]
            selected_row = df_paid[df_paid["No"] == selected_id]

            if not selected_row.empty:
                selected_row = selected_row.iloc[0]
                selected_event = next((event for event in timeline_events if event["id"] == selected_id), None)

                # 📌 사이드바에 선택된 항목 정보 표시
                st.sidebar.subheader("📌 선택된 항목 상세 정보")
                st.sidebar.markdown(f"### 🆔 No: {selected_id}")
                st.sidebar.markdown(f"**👤 이름:** {selected_row['이름']}")
                st.sidebar.markdown(f"**📅 기간:** {selected_event['weeks']}주")
                st.sidebar.markdown(f"**💰 합계금액:** {int(selected_row['합계금액']):,} 원")
                st.sidebar.markdown(f"**⏳ 남은 일수:** {selected_event['d_day_value']}일") 
                st.sidebar.markdown(f"**📅 주문일시:** {selected_row['주문일시']}")
                st.sidebar.markdown(f"**📝 주문명:** {selected_row['주문명']}")
                st.sidebar.markdown(f"**💳 결제구분:** {selected_row['결제구분']}")
                st.sidebar.markdown(f"**🛒 주문유형:** {selected_row['주문유형']}")
            else:
                st.sidebar.warning("🚨 선택한 주문 정보를 찾을 수 없습니다.")
    else:
        st.warning(f"🚨 현재 유효한 {title_map[page]} 이용 내역이 없습니다.")
    


    # 📌 D-Day 구간별 카운트 저장
    dday_binned_counts = {}

    for d_day_value, count in dday_counts.items():
        bin_label = categorize_dday(d_day_value)  # ✅ D-Day를 5명 단위로 그룹화
        if bin_label not in dday_binned_counts:
            dday_binned_counts[bin_label] = 0
        dday_binned_counts[bin_label] += count

    # 📌 D-Day 히스토그램 데이터프레임 생성 (정렬 순서 추가)
    dday_hist_df = pd.DataFrame(list(dday_binned_counts.items()), columns=["D-Day Group", "Count"])

    # ✅ D-Day 그룹을 올바른 순서로 정렬하기 위한 순서 지정
    dday_hist_df["Sort Order"] = dday_hist_df["D-Day Group"].map({
        "0~4": 1, "5~9": 2, "10~14": 3, "15~19": 4, "20~24": 5, "25~29": 6, "30+": 7
    })
    dday_hist_df = dday_hist_df.sort_values("Sort Order")  # ✅ 숫자 순서대로 정렬

    # 📌 D-Day 히스토그램 그래프
    st.subheader("📊 D-Day별 회원 수 (5명 단위)")
    chart = alt.Chart(dday_hist_df).mark_bar().encode(
        x=alt.X("D-Day Group:N", title="D-Day 구간", sort=list(dday_hist_df["D-Day Group"])),  # ✅ 정렬 순서 적용
        y=alt.Y("Count:Q", title="회원 수"),
        tooltip=["D-Day Group", "Count"]
    ).properties(width=800, height=400)

    st.altair_chart(chart)

# 📈 매출 페이지
elif page == "📈 매출":

    # 총 매출 (결제완료된 주문만 포함)
    st.title("📈 매출 현황")
    total_sales = df_paid["합계금액"].sum()
    nicepay_fee = total_sales * 0.033
    royalty_fee = total_sales * 0.05
    final_amount = total_sales - nicepay_fee - royalty_fee
    col1, col2 = st.columns(2)
    col1.metric("💰 총 매출 (결제완료)", f"{total_sales:,.0f} 원")
    col2.metric("💳 3.3% 나이스페이 수수료", f"-{nicepay_fee:,.0f} 원")
    col1.metric("🏛️ 5% 로열티", f"-{royalty_fee:,.0f} 원")
    col2.metric("✅ 최종 정산 금액", f"{final_amount:,.0f} 원")

    # 📌 "구분"별 매출 표시
    st.divider()
    st.title("📌 종류별 매출 현황")
    # 📌 "구분"별 매출 계산
    category_sales = df_paid.groupby("구분")["합계금액"].sum()  
    col3, col4 = st.columns(2)
    for idx, (category, sales) in enumerate(category_sales.items()):
        if idx % 2 == 0:
            col3.metric(f"{category} 매출", f"{sales:,.0f} 원")
        else:
            col4.metric(f"{category} 매출", f"{sales:,.0f} 원")

    # ✅ 퍼센트 값 계산 (각 항목의 비율)
    category_sales = category_sales.reset_index()
    category_sales["퍼센트"] = (category_sales["합계금액"] / category_sales["합계금액"].sum()) * 100
    category_sales["퍼센트"] = category_sales["퍼센트"].round(1)  # 소수점 1자리로 표시

    # 📌 "구분"별 매출 파이 차트
    pie_chart = alt.Chart(category_sales).mark_arc(innerRadius=50).encode(
        theta="합계금액:Q",
        color="구분:N",
        tooltip=["구분", "합계금액", "퍼센트"]
    ).properties(width=500, height=400)


    # 📌 차트 표시 (파이 차트 + 퍼센트 값)
    st.altair_chart(pie_chart)

# 🏆 회원별 결제 금액 페이지
elif page == "🏆 회원별 결제 금액":
    st.title("🏆 회원별 총 결제 금액 TOP 10")

    # 회원별 총 결제 금액 계산
    top_members = df_paid.groupby("이름")["합계금액"].sum().nlargest(10).reset_index()

    # Altair 차트 표시 (페이지 높이에 맞게 조정)
    chart = alt.Chart(top_members).mark_bar(color="skyblue").encode(
        x=alt.X("합계금액:Q", title="총 결제 금액 (원)"),
        y=alt.Y("이름:N", sort="-x", title="회원 이름")
    ).properties(width=800, height=600)

    st.altair_chart(chart)

elif page == "test":
    df_paid[["시간", "기간", "상품 유형", "이벤트명", "시작일", "종료일", "남은일수", "D-Day", "만료여부"]] = df.apply(process_order_row, axis=1)
    cols_to_show = [
        "구분", "이름", "주문명", "합계금액", "결제구분", "주문유형", "주문일시",
        "시간", "기간", "상품 유형", "이벤트명", "시작일", "종료일", "남은일수", "D-Day", "만료여부"
    ]
    st.write(df_paid[cols_to_show])