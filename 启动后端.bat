@echo off
chcp 65001 >nul
title 仲易达智能助手 - 后端服务
cd /d "%~dp0backend"
echo 正在启动后端服务...
venv\Scripts\python main.py
pause
