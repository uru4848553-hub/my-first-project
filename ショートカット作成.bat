@echo off
chcp 65001 >nul
rem デスクトップに、アイコン付きのアプリのショートカットを作る（最初に1回だけダブルクリック）
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\make_shortcut.ps1"
pause
