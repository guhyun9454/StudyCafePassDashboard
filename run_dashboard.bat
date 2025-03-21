@echo off
git pull origin main --force
call "C:\ProgramData\anaconda3\Scripts\activate.bat"
call conda activate dashboard
call pip install -r requirements.txt
streamlit run app.py
pause