@echo off
chcp 65001 >nul
rem 動画フォルダをこのファイルにドラッグ＆ドロップすると、自動編集を実行する
rem （Resolve を起動し、プロジェクトを開いておくこと）
cd /d "%~dp0"
if not exist "%~dp0run.bat" (
  echo [エラー] run.bat がありません。先に setup.ps1 を実行してください。
  pause
  exit /b 1
)
set "FOLDER=%~1"
if "%FOLDER%"=="" set /p "FOLDER=動画フォルダのパスを入力して Enter: "
if "%FOLDER%"=="" exit /b 1
set FOLDER=%FOLDER:"=%
call "%~dp0run.bat" "%~dp0autoedit.py" "%FOLDER%"
echo.
pause
