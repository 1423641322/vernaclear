@echo off
setlocal
cd /d "%~dp0"
set "VERNACLEAR_PORTABLE_ROOT=%~dp0"
set "PYTHONNOUSERSITE=1"
set "PYTHONUTF8=1"
start "Vernaclear" "%~dp0runtime\pythonw.exe" "%~dp0app\run.py" %*
