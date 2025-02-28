import streamlit as st

def init_page(title, layout="wide"):
    st.set_page_config(page_title=title, layout=layout)
    hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        </style>
    """
    st.markdown(hide_menu_style, unsafe_allow_html=True)

def categorize_dday(d_day_value):
    if d_day_value < 5:
        return "0~4"
    elif d_day_value < 10:
        return "5~9"
    elif d_day_value < 15:
        return "10~14"
    elif d_day_value < 20:
        return "15~19"
    elif d_day_value < 25:
        return "20~24"
    elif d_day_value < 30:
        return "25~29"
    else:
        return "30+"