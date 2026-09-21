@echo off
rem Double-click to open the FedCast front end.
cd /d "%~dp0"
".venv\Scripts\python.exe" -m fedcast.cli ui
