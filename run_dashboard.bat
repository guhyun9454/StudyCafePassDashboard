@echo off
cd /d C:\path\to\your\project  REM Git 프로젝트 폴더로 이동
echo 코드를 다운로드합니다.
git pull origin main  REM Git에서 최신 코드 가져오기

call "C:\ProgramData\Miniconda3\Scripts\activate.bat"
call conda activate dashboard  REM Conda 가상환경 활성화

echo 대시보드를 실행합니다.
streamlit run app.py  REM 파이썬 실행

pause  REM 실행 후 창이 닫히지 않도록 유지