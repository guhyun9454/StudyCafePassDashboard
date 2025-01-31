import streamlit as st
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="스터디 카페 대시보드", layout="wide")

hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
"""
st.markdown(hide_menu_style, unsafe_allow_html=True)


st.title("📂 파일 업로드")

# 업로드된 파일을 세션에 저장
uploaded_file = st.file_uploader("분석할 CSV 파일을 업로드하세요", type=["csv"])
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
    df = pd.read_csv(uploaded_file, encoding="euc-kr")
    st.session_state["df"] = df

    # 📌 컬럼 체크: 결제 로그 vs 회원 데이터
    payment_columns = {"No", "브랜드", "지점", "구분", "이름", "주문명", "주문금액", "할인금액", "합계금액", "결제구분", "주문유형", "주문상태", "주문일시"}
    member_columns = {"NO", "이름", "생년월일", "성별", "사물함", "신발장", "휴대폰", "PIN번호", "수신", "보호자", "휴대폰2", "수신2", "상태", "이용권", "좌석", "좌석타입", "시작일", "종료일", "잔여", "전체", "이용금액"}

    if payment_columns.issubset(df.columns):
        st.success("✅ 결제 로그 파일이 감지되었습니다. '💳 결제 로그' 페이지로 이동합니다.")
        st.session_state["file_type"] = "payment"
        st.rerun()
    elif member_columns.issubset(df.columns):
        st.success("✅ 회원 데이터 파일이 감지되었습니다. '👤 회원 분석' 페이지로 이동합니다.")
        st.session_state["file_type"] = "member"
        st.rerun()
    else:
        st.error("🚨 올바른 파일 형식이 아닙니다. 결제 로그 또는 회원 데이터를 업로드하세요.")
        st.session_state["file_type"] = None
else:
    st.session_state["file_type"] = None
