@echo off
REM BeeScout - Start semua layanan
cd /d "%~dp0..\.."

if not exist .env (
  echo [GAGAL] File .env belum ada.
  echo Jalankan dulu: scripts\install\setup.bat
  pause
  exit /b 1
)

docker info >nul 2>nul
if errorlevel 1 (
  echo [GAGAL] Docker belum jalan. Buka Docker Desktop dulu.
  pause
  exit /b 1
)

echo -- Menjalankan BeeScout ----------------------------------------
docker compose up -d
echo.
docker compose ps
echo.
echo   User  - http://app.localhost
echo   Admin - http://admin.localhost
echo.
pause
