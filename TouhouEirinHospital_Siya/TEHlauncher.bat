@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 东方永琳诊所 启动器
color 0F

echo ====================================================
echo             东方永琳诊所 ~Touhou Eirin Hospital~
echo ====================================================
echo.
echo(请选择 LLM 运行模式：
echo([A] 云端免费 API 模式 - 内置 Key
echo([B] 本地 Ollama 模式
echo([C] 云端 API 模式 - 自定义 Key
echo.
choice /C ABC /M "请输入选项（A / B / C）"

if errorlevel 3 goto API_CUSTOM
if errorlevel 2 goto LOCAL_MODE
if errorlevel 1 goto API_DEFAULT

:API_DEFAULT
set TEH_USE_API=true
set TEH_CUSTOM_KEY=false
goto RUN

:API_CUSTOM
echo.
echo 请输入您的 API Key (覆盖内置池):
set /p USER_KEY=
set TEH_USE_API=true
set TEH_CUSTOM_KEY=true
set TEH_API_KEYS=%USER_KEY%
goto RUN

:LOCAL_MODE
set TEH_USE_API=false
set TEH_CUSTOM_KEY=false
goto RUN

:RUN
echo.
echo 正在启动加载器...
python TEHrunner.py --load
pause