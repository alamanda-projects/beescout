@echo off
REM BeeScout - Stop semua layanan
cd /d "%~dp0..\.."

echo -- Menghentikan BeeScout ---------------------------------------
docker compose down
echo.
echo   Selesai. Data MongoDB tetap aman.
echo   Untuk start lagi: scripts\install\start.bat
echo.
pause
