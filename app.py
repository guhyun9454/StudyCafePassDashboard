import streamlit as st

pages = dict()

# 📌 파일 유형에 따라 동적으로 페이지 추가
if "file_type" in st.session_state:
    if st.session_state["file_type"] == "payment":
        pages["💳 결제 로그"] = [st.Page("pages/payments.py", title="결제 로그")]
    elif st.session_state["file_type"] == "member":
        pages["👤 회원"] = [st.Page("pages/members.py", title="회원 분석")]
    else:
        pages["📂 업로드"] =  [st.Page("pages/upload.py", title="업로드")]
else:
    pages["📂 업로드"] =  [st.Page("pages/upload.py", title="업로드")]

# 📌 네비게이션 실행
pg = st.navigation(pages)
pg.run()