import streamlit as st
import pandas as pd
from utils import init_page
init_page("👤 회원 분석")


if "df" not in st.session_state:
    st.warning("🚨 먼저 홈에서 파일을 업로드해주세요.")
    st.stop()

# 🔄 초기화 & 업로드 페이지로 이동하는 버튼
if st.sidebar.button("🔄 다시 업로드하기"):
    st.session_state.clear()  # 세션 초기화
    st.rerun()  # 업로드 페이지로 이동
st.sidebar.title("📌 메뉴")

st.title("👤 회원 분석 페이지")
st.info("🚧 회원 분석 기능은 현재 개발 중입니다.")

df = st.session_state["df"]

# 📌 "결제완료" 상태의 주문만 필터링
df = df[df["이름"] != "관리자"]

st.dataframe(df)
