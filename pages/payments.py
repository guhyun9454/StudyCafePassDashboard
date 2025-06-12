import streamlit as st
import pandas as pd
import altair as alt
from streamlit_timeline import st_timeline
import re
from datetime import datetime
import calendar

from events import process_order_row
from utils import categorize_dday, init_page
from event_utils import calc_normal_sales_estimate
init_page("💳 결제 로그 분석")

cols_to_show = [
    "구분", "이름", "주문명", "합계금액", "결제구분", "주문유형", "주문일시",
    "시간", "기간", "상품 유형", "이벤트명", "시작일", "종료일", "남은일수", "D-Day", "만료여부"
]

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
    ["📈 매출", "📊 월별 통계", "🎉 이벤트 현황", "📅 기간권", "🏆 회원별 결제 금액","데이터 보기"]
)


df = st.session_state["df"]

# 날짜 변환
df["주문일시"] = pd.to_datetime(df["주문일시"], errors="coerce")

# 📌 "결제완료" 상태의 주문만 필터링
df_paid = df[(df["주문상태"] == "결제완료") & (df["이름"] != "관리자")]
df_paid[["시간", "기간", "상품 유형", "이벤트명", "시작일", "종료일", "남은일수", "D-Day", "만료여부"]] = df.apply(process_order_row, axis=1)

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
if page == "📅 기간권":
    st.title(f"📅 기간권 이용 내역")
    st.caption("💡 타임라인 속 각 항목을 클릭하면 왼쪽에서 상세한 결제 정보를 확인할 수 있습니다.")
    # 📅 현재 날짜
    today = datetime.today().date()

    # 📌 사용자별 한 줄 표시를 고정하고, 관련 체크박스를 제거했습니다.
    show_expired = st.sidebar.checkbox("만료된 기간권 보기", value=False)
    st.sidebar.divider()
    search_name = st.sidebar.text_input("🔍 회원 검색 (이름 입력)", "")


    # 📌 타임라인 데이터 생성 (만료된 데이터 선택적으로 제외)
    timeline_df = df_paid[df_paid["구분"] == "기간권"].copy()

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
                    "style": "background-color: pink; color: black; border-color: red" if end_date_obj < today else "background-color: #caf0f8; color: black; border-color: #caf0f8"
                }
                timeline_events.append(event)
                valid_users.add(row["이름"])  # ✅ 실제 표시할 데이터가 있는 사용자만 그룹으로 포함

    # ✅ D-Day 값이 작은 순으로 이벤트 정렬 (남은 기간이 적은 회원이 위쪽에 보이도록)
    timeline_events.sort(key=lambda x: x["d_day_value"])

    if valid_users:
        # ✅ 사용자별 최소 D-Day 값을 기준으로 그룹을 정렬
        user_min_dday = {}
        for ev in timeline_events:
            user_min_dday[ev["name"]] = min(user_min_dday.get(ev["name"], float("inf")), ev["d_day_value"])

        # D-Day 오름차순으로 사용자 정렬
        sorted_users = sorted(user_min_dday.items(), key=lambda x: x[1])

        groups = [{"id": idx, "content": name} for idx, (name, _) in enumerate(sorted_users)]
        user_id_map = {g["content"]: g["id"] for g in groups}  # ✅ 사용자 이름 → ID 매핑

        for event in timeline_events:
            event["group"] = user_id_map[event["name"]]  # ✅ 그룹 ID 적용
    else:
        groups = []

    # ✨ 이벤트 기간(background) 추가 표시
    from event_utils import event_configs
    for evt_name, config in event_configs.items():
        evt_start = config["이벤트기간"][0].date().isoformat()
        evt_end = config["이벤트기간"][1].date().isoformat()
        timeline_events.append({
            "id": f"event_{evt_name}",
            "content": evt_name,
            "start": evt_start,
            "end": evt_end,
            "type": "background",
            "style": "background-color: rgba(144, 224, 239, 0.15);"
        })

    # 📌 D-Day가 0 이상인 회원 수 표시
    st.metric("기간 남은 회원 수", f"{future_count} 명")

    # 📌 타임라인 표시
    if timeline_events:
        # ℹ️ 타임라인 높이를 2배(1200px)로 늘리고, 이벤트 기간(background)도 함께 표시합니다.
        timeline = st_timeline(
            timeline_events,
            groups=groups,
            options={'orientation': 'top'},
            height="1000px"
        )

        if timeline:
            selected_id = timeline["id"]
            # 이벤트 기간(background) 등 정수가 아닌 ID는 무시
            if isinstance(selected_id, int):
                selected_row = df_paid[df_paid["No"] == selected_id]
            else:
                selected_row = pd.DataFrame()

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
                # 이벤트 여부 정보 표시
                st.sidebar.markdown(f"**🎯 이벤트 여부:** {selected_row['상품 유형']}")
                if pd.notnull(selected_row.get('이벤트명')):
                    st.sidebar.markdown(f"**🏷️ 이벤트명:** {selected_row['이벤트명']}")
            else:
                st.sidebar.warning("🚨 선택한 주문 정보를 찾을 수 없습니다.")
    else:
        st.warning(f"🚨 현재 유효한 기간권 이용 내역이 없습니다.")
    


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
    st.subheader("📊 남은 기간별 회원 수")
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
    st.subheader("📌 종류별 매출 현황")
    
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
    st.subheader("📊 매출 구성비")
    pie_chart = alt.Chart(category_sales).mark_arc(innerRadius=50).encode(
        theta="합계금액:Q",
        color="구분:N",
        tooltip=["구분", "합계금액", "퍼센트"]
    ).properties(width=500, height=400)

    # 📌 차트 표시 (파이 차트 + 퍼센트 값)
    st.altair_chart(pie_chart)
    
    # 📌 일별 매출 추이
    st.subheader("📈 일별 매출 추이")
    
    # 일별 매출 계산
    daily_sales = df_paid.groupby(df_paid["주문일시"].dt.date)["합계금액"].sum().reset_index()
    daily_sales.columns = ["날짜", "매출"]
    daily_sales["날짜"] = pd.to_datetime(daily_sales["날짜"])
    
    # 일별 매출 차트
    daily_chart = alt.Chart(daily_sales).mark_line(point=True).encode(
        x=alt.X("날짜:T", title="날짜"),
        y=alt.Y("매출:Q", title="매출 (원)"),
        tooltip=["날짜:T", "매출:Q"]
    ).properties(width=800, height=400)
    
    st.altair_chart(daily_chart)


# 📊 월별 통계 페이지
elif page == "📊 월별 통계":
    st.title("📊 월별 통계")

    # 📌 월별 데이터 준비
    df_paid["연월"] = df_paid["주문일시"].dt.to_period("M")

    # 📌 월별 통계 계산 (원본 "구분" 컬럼 사용)
    monthly_stats = df_paid.groupby(["연월", "구분"]).agg({
        "합계금액": ["sum", "count"]
    }).reset_index()

    # 컬럼명 정리
    monthly_stats.columns = ["연월", "구분", "매출", "건수"]
    monthly_stats["연월_str"] = monthly_stats["연월"].astype(str)

    # 📌 필터링 옵션
    st.sidebar.subheader("📌 월별 통계 옵션")

    # 연도 선택만 유지
    years = sorted(df_paid["주문일시"].dt.year.unique())
    selected_year = st.sidebar.selectbox("📅 연도 선택", ["전체"] + list(years))

    if selected_year != "전체":
        monthly_stats = monthly_stats[monthly_stats["연월"].dt.year == selected_year]
        df_filtered = df_paid[df_paid["주문일시"].dt.year == selected_year]
    else:
        df_filtered = df_paid

    # 📌 월별 총 매출 계산 (매출 추이 그래프용)
    monthly_total = monthly_stats.groupby("연월_str")["매출"].sum().reset_index()
    monthly_total["최종정산금액"] = monthly_total["매출"] * 0.912  # 8.8% 수수료 제외

    # 📌 현재 월 예상 매출 및 실제 매출 계산
    today = datetime.today()
    current_year_month_str = today.strftime("%Y-%m")
    current_period = pd.Period(current_year_month_str)
    current_month_df = df_filtered[df_filtered["주문일시"].dt.to_period("M") == current_period]

    current_actual_point = None
    if not current_month_df.empty:
        current_sales = current_month_df["합계금액"].sum()
        elapsed_days = today.day
        total_days_in_month = calendar.monthrange(today.year, today.month)[1]
        if elapsed_days > 0:
            predicted_sales = (current_sales / elapsed_days) * total_days_in_month
            predicted_settlement = predicted_sales * 0.912

            if (monthly_total["연월_str"] == current_year_month_str).any():
                monthly_total.loc[monthly_total["연월_str"] == current_year_month_str, "매출"] = predicted_sales
                monthly_total.loc[monthly_total["연월_str"] == current_year_month_str, "최종정산금액"] = predicted_settlement
            else:
                monthly_total = pd.concat([monthly_total, pd.DataFrame({
                    "연월_str": [current_year_month_str],
                    "매출": [predicted_sales],
                    "최종정산금액": [predicted_settlement]
                })], ignore_index=True)

            current_actual_point = {
                "연월_str": current_year_month_str,
                "금액": current_sales
            }

    # 월별 정렬
    monthly_total = monthly_total.sort_values("연월_str")

    # 📈 월별 매출 추이 그래프
    st.subheader("📈 월별 매출 추이")
    
    if not monthly_total.empty:
        # 매출과 최종 정산 금액을 함께 표시할 데이터 준비
        monthly_melted = monthly_total.melt(
            id_vars=["연월_str"], 
            value_vars=["매출", "최종정산금액"],
            var_name="구분", 
            value_name="금액"
        )
        
        # 기본 선 그래프 (실선: 과거 월, 점선: 전월→현재월)
        prev_period = current_period - 1
        prev_month_str = str(prev_period)

        # ✅ 실선: 1~전월 데이터
        actual_melted = monthly_melted[monthly_melted["연월_str"] <= prev_month_str]
        solid_line = alt.Chart(actual_melted).mark_line(point=True).encode(
            x=alt.X("연월_str:N", title="월", sort=None),
            y=alt.Y("금액:Q", title="금액 (원)"),
            color=alt.Color("구분:N", 
                           scale=alt.Scale(domain=["매출", "최종정산금액"], 
                                         range=["blue", "green"]),
                           title="구분"),
            tooltip=["연월_str:N", "구분:N", alt.Tooltip("금액:Q", format=",.0f")]
        )

        # ✅ 점선: 전월→현재월(예상) 연결
        predicted_melted = monthly_melted[monthly_melted["연월_str"].isin([prev_month_str, current_year_month_str])]
        dashed_line = alt.Chart(predicted_melted).mark_line(point=True, strokeDash=[4,4]).encode(
            x="연월_str:N",
            y="금액:Q",
            color=alt.Color("구분:N", 
                           scale=alt.Scale(domain=["매출", "최종정산금액"], 
                                         range=["blue", "green"]),
                           title="구분"),
            tooltip=["연월_str:N", "구분:N", alt.Tooltip("금액:Q", format=",.0f")]
        )

        trend_chart_base = solid_line + dashed_line

        # 현재 월 실제 매출을 빨간 점으로 표시
        if current_actual_point:
            point_chart = alt.Chart(pd.DataFrame([current_actual_point])).mark_point(
                size=150, color="red"
            ).encode(
                x="연월_str:N",
                y="금액:Q",
                tooltip=["연월_str:N", alt.Tooltip("금액:Q", format=",.0f")]
            )
            trend_chart = (trend_chart_base + point_chart).properties(width=800, height=400, title="월별 매출 및 최종 정산 금액 추이")
        else:
            trend_chart = trend_chart_base.properties(width=800, height=400, title="월별 매출 및 최종 정산 금액 추이")

        st.altair_chart(trend_chart)
        st.caption("💡 실선은 월말까지의 예상 매출·정산 금액이고, 빨간 점은 오늘까지의 실제 누적 매출입니다.")
        
        # 📊 월별 매출 요약 통계
        col1, col2, col3 = st.columns(3)
        
        total_revenue = monthly_total["매출"].sum()
        total_final = monthly_total["최종정산금액"].sum()
        avg_monthly = monthly_total["매출"].mean()
        
        with col1:
            st.metric("총 매출", f"{total_revenue:,.0f} 원")
        with col2:
            st.metric("총 최종 정산 금액", f"{total_final:,.0f} 원")
        with col3:
            st.metric("월평균 매출", f"{avg_monthly:,.0f} 원")

    # 📊 월별 매출 현황
    st.subheader("📈 월별 매출 현황")

    if not monthly_stats.empty:
        # 매출 막대 그래프
        revenue_chart = alt.Chart(monthly_stats).mark_bar().encode(
            x=alt.X("연월_str:N", title="월", sort=None),
            y=alt.Y("매출:Q", title="매출 (원)"),
            color=alt.Color("구분:N", title="상품 유형"),
            tooltip=["연월_str:N", "구분:N", "매출:Q", "건수:Q"]
        ).properties(width=800, height=400, title="월별 매출")

        st.altair_chart(revenue_chart)
        
        # 📊 월별 판매 건수 그래프
        st.subheader("📊 월별 판매 건수")
        
        # 🔍 상품 유형 필터 (st.pills)
        pill_options = sorted(monthly_stats["구분"].unique().tolist())
        selected_categories = st.pills(
            "표시할 상품 유형 선택",
            options=pill_options,
            selection_mode="multi",
            default=pill_options
        )

        filtered_monthly_stats = monthly_stats[monthly_stats["구분"].isin(selected_categories)]

        if filtered_monthly_stats.empty:
            st.info("❗ 표시할 상품 유형을 선택해주세요.")
        else:
            count_chart = alt.Chart(filtered_monthly_stats).mark_line(point=True).encode(
                x=alt.X("연월_str:N", title="월", sort=None),
                y=alt.Y("건수:Q", title="판매 건수"),
                color=alt.Color("구분:N", title="상품 유형"),
                tooltip=["연월_str:N", "구분:N", "건수:Q", "매출:Q"]
            ).properties(width=800, height=400, title="월별 판매 건수")
            
            st.altair_chart(count_chart)

    else:
        st.warning("🚨 선택된 조건에 해당하는 데이터가 없습니다.")

# 🎉 이벤트 현황 페이지
elif page == "🎉 이벤트 현황":
    st.title("🎉 이벤트 현황")

    st.caption("🔍 기간권 (2주, 4주 등), 정액시간권(50시간, 100시간 등)만 집계됩니다.")

    # 📌 이벤트별 매출 표시
    normal_sales = df_paid[df_paid["상품 유형"] == "정가"]["합계금액"].sum()
    col1, col2 = st.columns(2)

    event_df = df_paid[df_paid["이벤트명"].notnull()]

    if not event_df.empty:
        # 이벤트별 상세 매출 데이터
        event_sales_detail = event_df.groupby(["이벤트명", "상품 유형"])["합계금액"].sum().reset_index()
        event_total_sales = event_df.groupby("이벤트명")["합계금액"].sum().reset_index()

        # 전체 정가 매출 요약 출력 (한 번만)
        normal_df = df_paid[df_paid["상품 유형"] == "정가"]
        if not normal_df.empty:
            normal_sales = normal_df["합계금액"].sum()
            total_days = (max_date - min_date).days + 1
            avg_normal_sales_per_day = normal_sales / total_days
            
            with col1:
                st.metric(f"✅ 정가 매출 - {total_days}일간 발생", f"{normal_sales:,.0f} 원")
            with col2:
                st.metric("📊 일주일 평균 정가 매출", f"{avg_normal_sales_per_day * 7:,.0f} 원")

        # 이벤트 매출 표시 (delta는 유지)
        for i, (_, row) in enumerate(event_total_sales.iterrows()):
            event_name = row["이벤트명"]
            actual_event_sales = row["합계금액"]

            estimated_normal_sales, event_duration, _, _ = calc_normal_sales_estimate(
                event_name, normal_df, min_date, max_date
            )

            target_col = col1 if i % 2 == 0 else col2
            with target_col:
                st.metric(
                    f"{event_name} 이벤트 매출 - {event_duration}일간 진행",
                    f"{actual_event_sales:,.0f} 원",
                    delta=f"{actual_event_sales - estimated_normal_sales:,.0f} 원"
                )
        
        # 📌 이벤트별 매출 차트
        st.subheader("📈 이벤트별 매출 비교")
        chart_event = alt.Chart(event_sales_detail).mark_bar().encode(
            x=alt.X("이벤트명:N", title="이벤트명"),
            y=alt.Y("합계금액:Q", title="매출 (원)"),
            color=alt.Color("상품 유형:N", 
                           scale=alt.Scale(domain=["이벤트", "이벤트 의심"], 
                                         range=["orange", "red"]), 
                           title="상품 유형"),
            tooltip=["이벤트명", "상품 유형", "합계금액"]
        ).properties(width=800, height=400)
        st.altair_chart(chart_event)

    else:
        st.warning("🚨 이벤트 매출 데이터가 없습니다.")

    # 📌 이벤트 의심 회원 분석
    
    suspected_df = df_paid[df_paid["상품 유형"] == "이벤트 의심"]
    if not suspected_df.empty:

        st.subheader("📋 이벤트 의심 상세 내역")
        st.dataframe(suspected_df[cols_to_show], use_container_width=True)
    else:
        st.success("✅ 이벤트 의심 회원이 없습니다.")

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

elif page == "데이터 보기":

    st.write(df_paid[cols_to_show])