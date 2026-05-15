@echo off
REM BeeScout - Start semua layanan
cd /d "%~dp0..\.."
set FIRST_RUN=0

if not exist .env (
  echo [INFO] File .env belum ada. Membuat konfigurasi lokal...
  copy .env.example .env >nul
  set FIRST_RUN=1
  powershell -NoProfile -Command "$p='.env'; $c=Get-Content $p -Raw; $mongo=(-join ((48..57)+(65..90)+(97..122) | Get-Random -Count 24 | ForEach-Object {[char]$_})); $c=$c.Replace('MONGODB_PASS=changeme_strong_password_here','MONGODB_PASS='+$mongo); $c=$c.Replace('TKN_SECRET_KEY=changeme_generate_with_openssl_rand_hex_32','TKN_SECRET_KEY='+([guid]::NewGuid().ToString('N')+[guid]::NewGuid().ToString('N'))); $c=$c.Replace('TKN_SECRET_TOKEN=changeme_generate_with_openssl_rand_hex_32','TKN_SECRET_TOKEN='+([guid]::NewGuid().ToString('N')+[guid]::NewGuid().ToString('N'))); $c=$c.Replace('SA_SECRET_KEY=changeme_generate_with_openssl_rand_hex_32','SA_SECRET_KEY='+([guid]::NewGuid().ToString('N')+[guid]::NewGuid().ToString('N'))); $c=$c.Replace('SA_SECRET_TOKEN=changeme_generate_with_openssl_rand_hex_32','SA_SECRET_TOKEN='+([guid]::NewGuid().ToString('N')+[guid]::NewGuid().ToString('N'))); $c=$c.Replace('COOKIE_SECURE=true','COOKIE_SECURE=false'); Set-Content $p $c"
  echo [OK] .env dibuat dan secret lokal di-generate.
)

docker info >nul 2>nul
if errorlevel 1 (
  echo [GAGAL] Docker belum jalan. Buka Docker Desktop dulu.
  pause
  exit /b 1
)

echo -- Menjalankan BeeScout ----------------------------------------
if "%FIRST_RUN%"=="1" (
  docker compose up --build -d
) else (
  docker compose up -d
)
echo.
docker compose ps
echo.
echo   User       - http://app.localhost
echo   Admin      - http://admin.localhost
echo   Setup Awal - http://admin.localhost/setup
echo.
pause
