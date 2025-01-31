import streamlit as st
import pandas as pd
import os

# Streamlit 페이지 설정
st.set_page_config(page_title="스터디 카페 대시보드", layout="wide")

# 📌 사이드바 메뉴
st.sidebar.title("📌 메뉴 선택")
st.sidebar.info("파일을 업로드한 후 자동으로 해당 페이지로 이동합니다.")

# 파일 업로드
uploaded_file = st.file_uploader("📂 CSV 파일을 업로드하세요", type=["csv"])
if uploaded_file is None:
    st.info(
        """
        📢 **엑셀 파일 업로드 안내**
        
        1. **[픽코] → [설정] → [회원관리] → [회원결제내역]** 메뉴로 이동하세요.
        2. 구분, 상태, 결제 타입을 **전체**로 선택하세요.
        3. 집계를 **원하는 기간**을 선택하세요.
        4. **엑셀 파일을 다운로드**후 업로드하세요.

        🔥 **주의 사항**
        
        - 전화번호 뒷자리가 같아 이름이 같은 경우 **같은 사람으로 집계될 수 있습니다.**
        - 개별 회원을 구별하려면 픽코에서 **이름을 수동으로 수정**해야 합니다.
        """
    )
if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, encoding="euc-kr")
    except UnicodeDecodeError:
        st.error("⚠️ CSV 파일 인코딩 오류! UTF-8 형식인지 확인해주세요.")
        st.stop()

    # 📌 컬럼 확인하여 페이지 이동 결정
    payment_columns = ["No", "브랜드", "지점", "구분", "이름", "주문명", "주문금액", "할인금액", "합계금액", "결제구분", "주문유형", "주문상태", "주문일시"]
    member_columns = ["NO", "이름", "생년월일", "성별", "사물함", "신발장", "휴대폰", "PIN번호", "수신", "보호자", "휴대폰2", "수신2", "상태", "이용권", "좌석", "좌석타입", "시작일", "종료일", "잔여", "전체", "이용금액"]

    if all(col in df.columns for col in payment_columns):
        st.session_state["df"] = df
        st.switch_page("pages/payments.py")  # 결제 로그 페이지로 이동
    elif all(col in df.columns for col in member_columns):
        st.session_state["df"] = df
        st.switch_page("pages/members.py")  # 회원 분석 페이지로 이동
    else:
        st.error("🚨 올바른 데이터 형식이 아닙니다. 결제 로그 또는 회원 정보 파일을 업로드하세요.")