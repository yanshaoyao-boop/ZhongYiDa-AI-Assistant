@echo off
chcp 65001 >nul
title 浠叉槗杈炬櫤鑳藉姪鎵?- 鍚庣鏈嶅姟
cd /d "%~dp0backend"
echo 姝ｅ湪鍚姩鍚庣鏈嶅姟...
set HOST=127.0.0.1
set UVICORN_RELOAD=0
venv\Scripts\python main.py
pause
