import streamlit as st
import pandas as pd
import altair as alt
from streamlit_timeline import st_timeline
import re
from datetime import datetime

# Streamlit 설정
st.set_page_config(page_title="스터디 카페 대시보드", layout="wide")

# 📌 사이드바에서 페이지 선택
st.sidebar.title("📌 메뉴 선택")
page = st.sidebar.radio(
    "이동할 페이지를 선택하세요",
    ["📈 매출", "📅 기간권", "📅 사물함", "🏆 회원별 결제 금액"]
)

# 📢 업로드 안내
st.info(
    """
    📢 **엑셀 파일 업로드 전 안내**
    
    1. **[피코] → [설정] → [회원관리] → [회원결제내역]** 메뉴로 이동하세요.
    2. 원하는 기간을 선택한 후 **엑셀 파일을 다운로드**하세요.
    """
)
uploaded_file = st.file_uploader("엑셀 파일을 업로드하세요", type=["csv"])

if uploaded_file is not None:
    
    # EUC-KR 인코딩 적용
    try:
        df = pd.read_csv(uploaded_file, encoding="euc-kr")
    except UnicodeDecodeError:
        st.error("⚠️ CSV 파일 인코딩 오류! UTF-8 형식인지 확인해주세요.")
        st.stop()

    # 날짜 변환
    df["주문일시"] = pd.to_datetime(df["주문일시"], errors="coerce")

    # 📌 "결제완료" 상태의 주문만 필터링
    df_paid = df[(df["주문상태"] == "결제완료") & (df["이름"] != "관리자")]

    # 📌 데이터의 첫 주문일시 & 마지막 주문일시 감지
    min_date = df["주문일시"].min().date() if not df["주문일시"].isna().all() else None
    max_date = df["주문일시"].max().date() if not df["주문일시"].isna().all() else None

    # 📌 데이터 기간 + 현재 날짜 기준 필터링 안내 추가
    if min_date and max_date:
        st.info(f"📆 **이 데이터는 {min_date}부터 {max_date}까지의 주문 내역입니다.** ")

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

        # 📅 현재 날짜
        today = datetime.today().date()
        st.info(f"오늘 날짜 (**{today}**)를 기준으로 **만료된 기간권은 제외**되었습니다.")

        # 📌 타임라인 데이터 생성 (만료된 데이터 제외 + 남은 D-Day 추가)
        timeline_df = df_paid[df_paid["구분"] == title_map[page]].copy()
        timeline_events = []
        for _, row in timeline_df.iterrows():
            start_date, end_date = extract_dates(row["주문명"])
            
            if start_date and end_date:
                # 문자열을 datetime.date로 변환
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()

                if end_date_obj >= today:  # 현재 날짜보다 종료일이 이후인 경우만 포함
                    # 남은 D-Day 계산
                    d_day = (end_date_obj - today).days
                    event = {
                        "id": int(row["No"]),
                        "content": f"{row['이름']}: (D-{d_day})",
                        "start": start_date,
                        "end": end_date,
                    }
                    timeline_events.append(event)

        # 📌 타임라인 표시
        if timeline_events:
            timeline = st_timeline(timeline_events, groups=[], options={}, height="600px")

            # 선택된 ID를 기반으로 데이터 출력
            if timeline:
                selected_id = timeline["id"]  # 선택된 주문의 No 값
                selected_row = df_paid[df_paid["No"] == selected_id]  # ✅ No 값과 일치하는 행 찾기

                if not selected_row.empty:
                    selected_row = selected_row.iloc[0]  # 첫 번째 결과 가져오기

                    # 📌 사이드바에 선택된 항목 정보 표시
                    st.sidebar.subheader("📌 선택된 항목 상세 정보")
                    st.sidebar.markdown(f"### 🆔 No: {selected_id}")
                    st.sidebar.markdown(f"**👤 이름:** {selected_row['이름']}")
                    st.sidebar.markdown(f"**📌 구분:** {selected_row['구분']}")
                    st.sidebar.markdown(f"**📝 주문명:** {selected_row['주문명']}")
                    st.sidebar.markdown(f"**💰 합계금액:** {int(selected_row['합계금액']):,} 원")
                    st.sidebar.markdown(f"**💳 결제구분:** {selected_row['결제구분']}")
                    st.sidebar.markdown(f"**🛒 주문유형:** {selected_row['주문유형']}")
                    st.sidebar.markdown(f"**📅 주문일시:** {selected_row['주문일시']}")
                else:
                    st.sidebar.warning("🚨 선택한 주문 정보를 찾을 수 없습니다.")
        else:
            st.warning(f"🚨 현재 유효한 {title_map[page]} 이용 내역이 없습니다.")

    # 📈 매출 페이지
    elif page == "📈 매출":
        st.title("📈 매출 정산 내역")

        # 총 매출 (결제완료된 주문만 포함)
        total_sales = df_paid["합계금액"].sum()
        nicepay_fee = total_sales * 0.033
        royalty_fee = total_sales * 0.05
        final_amount = total_sales - nicepay_fee - royalty_fee

        col1, col2 = st.columns(2)
        col1.metric("💰 총 매출 (결제완료)", f"{total_sales:,.0f} 원")
        col2.metric("💳 3.3% 나이스페이 수수료", f"-{nicepay_fee:,.0f} 원")
        col1.metric("🏛️ 5% 로열티", f"-{royalty_fee:,.0f} 원")
        col2.metric("✅ 최종 정산 금액", f"{final_amount:,.0f} 원")

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