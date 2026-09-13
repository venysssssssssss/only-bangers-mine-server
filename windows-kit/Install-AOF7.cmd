@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-AOF7.ps1" %*
exit /b %ERRORLEVEL%
