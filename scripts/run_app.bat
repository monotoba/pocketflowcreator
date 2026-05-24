@echo off
cd /d %~dp0\..
if not exist .venv (
  echo Missing .venv. Run scripts\setup-prj.bat first.
  exit /b 1
)
.venv\Scripts\pocketflow-creator.exe %*
