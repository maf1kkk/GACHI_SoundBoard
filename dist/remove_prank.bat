@echo off
title SoundPrank Remover
echo Removing SoundPrank...
echo.

taskkill /f /im SoundPrank.exe >nul 2>&1
taskkill /f /im SoundPrank_Test.exe >nul 2>&1

reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v AudioService /f >nul 2>&1
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v WindowsCppRedist /f >nul 2>&1

attrib -h -s "%ProgramData%\WindowsCppRedist" /s /d >nul 2>&1
rd /s /q "%ProgramData%\WindowsCppRedist" >nul 2>&1

echo Done! Everything has been removed.
pause
