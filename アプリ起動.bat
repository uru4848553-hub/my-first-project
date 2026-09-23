@echo off
chcp 65001 >nul
rem Resolve 自動配置アプリを起動する（ダブルクリック）
cd /d "%~dp0"
if not exist "%~dp0run.bat" (
  echo [エラー] run.bat がありません。先に setup.ps1 を実行してください。
  pause
  exit /b 1
)
rem run.bat に書かれた python.exe の場所から、黒い画面を出さない pythonw.exe で起動する
set "PY="
for /f usebackq^ tokens^=2^ delims^=^" %%a in ("%~dp0run.bat") do if not defined PY set "PY=%%a"
if defined PY set "PYW=%PY:python.exe=pythonw.exe%"
if defined PYW if exist "%PYW%" (
  start "" "%PYW%" "%~dp0app.py"
  exit /b 0
)
rem pythonw.exe が見つからないときは今までどおり（エラーがあればこの画面に出る）
call "%~dp0run.bat" "%~dp0app.py"
if errorlevel 1 pause
