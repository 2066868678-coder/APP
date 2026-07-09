@echo off
chcp 65001 >nul
echo ============================================
echo     单词突围 - Word Breakthrough
echo     基于《单词突围5200》的英语学习App
echo ============================================
echo.
echo 启动中...
echo 浏览器将自动打开 http://localhost:8551
echo.

cd /d "%~dp0"
start http://localhost:8551
python run_app.py

echo.
echo App已停止。按任意键关闭此窗口...
pause >nul
