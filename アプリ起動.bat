@echo off
chcp 65001 >nul
rem Resolve 自動配置アプリを起動する（ダブルクリック）
cd /d "%~dp0"
if not exist "%~dp0run.bat" (
  echo [エラー] run.bat がありません。先に setup.ps1 を実行してください。
  pause
  exit /b 1
)
call "%~dp0run.bat" "%~dp0app.py"
if errorlevel 1 pause
