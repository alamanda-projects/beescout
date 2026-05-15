@echo off
REM BeeScout - Setup Wizard untuk Windows
REM Klik dua kali file ini untuk menjalankan setup pertama kali.

setlocal EnableDelayedExpansion
cd /d "%~dp0..\.."
set "REPO_ROOT=%CD%"

echo.
echo ==============================================================
echo   BeeScout Setup Wizard (Windows)
echo ==============================================================
echo   Folder repo: %REPO_ROOT%
echo.

REM ── Langkah 1: Cek Docker ──────────────────────────────────────
echo --------------------------------------------------------------
echo   Langkah 1/4 - Cek Docker
echo --------------------------------------------------------------

where docker >nul 2>nul
if errorlevel 1 (
  echo   [GAGAL] Docker belum terinstall.
  echo.
  echo   Silakan install Docker Desktop dari:
  echo     https://www.docker.com/products/docker-desktop/
  echo.
  echo   Setelah install, buka Docker Desktop dan tunggu sampai
  echo   status hijau, lalu jalankan file ini lagi.
  goto :end
)
echo   [OK] Docker terinstall.

docker info >nul 2>nul
if errorlevel 1 (
  echo   [GAGAL] Docker belum jalan.
  echo   Buka aplikasi Docker Desktop dan tunggu sampai status hijau.
  goto :end
)
echo   [OK] Docker daemon berjalan.

REM ── Langkah 2: Setup .env ──────────────────────────────────────
echo.
echo --------------------------------------------------------------
echo   Langkah 2/4 - Konfigurasi .env
echo --------------------------------------------------------------

if exist .env (
  echo   [SKIP] .env sudah ada, tidak ditimpa.
) else (
  copy .env.example .env >nul
  echo   [OK] .env dibuat dari .env.example.
  echo.
  echo   [PENTING] Sebelum production, buka file .env dan ganti
  echo   semua nilai 'changeme_*' dengan password kuat.
  echo   Untuk dev lokal, default cukup dipakai dulu, tapi
  echo   ubah COOKIE_SECURE=true menjadi COOKIE_SECURE=false.
  echo.
  echo   Buka .env dengan Notepad sekarang? [Y/N]
  set /p OPEN_ENV=
  if /i "!OPEN_ENV!"=="Y" notepad .env
)

REM ── Langkah 3: Build & Start ───────────────────────────────────
echo.
echo --------------------------------------------------------------
echo   Langkah 3/4 - Build dan Jalankan Layanan
echo --------------------------------------------------------------
echo   Proses ini bisa 5-15 menit di first run (download image).
echo.

docker compose up --build -d
if errorlevel 1 (
  echo   [GAGAL] Tidak bisa start layanan. Cek pesan error di atas.
  goto :end
)
echo   [OK] Semua layanan berjalan.
echo.
docker compose ps

REM ── Langkah 4: hosts file ──────────────────────────────────────
echo.
echo --------------------------------------------------------------
echo   Langkah 4/4 - Konfigurasi file hosts
echo --------------------------------------------------------------
echo.
echo   Tambah 2 baris berikut ke file:
echo     C:\Windows\System32\drivers\etc\hosts
echo.
echo     127.0.0.1   app.localhost
echo     127.0.0.1   admin.localhost
echo.
echo   Cara: buka Notepad sebagai Administrator, lalu buka file
echo   hosts di atas, tambah 2 baris, simpan.
echo.
echo   (Otomatisasi langkah ini butuh hak admin - dilakukan manual.)
echo.

REM ── Selesai ────────────────────────────────────────────────────
echo ==============================================================
echo   Selesai!
echo ==============================================================
echo.
echo   Buka browser:
echo     Aplikasi User  - http://app.localhost
echo     Panel Admin    - http://admin.localhost
echo.
echo   Akun belum ada - lihat docs/quick-start-non-tech.md
echo   untuk cara membuat akun Super Admin pertama.
echo.
echo   Perintah berikutnya:
echo     scripts\install\start.bat - start lagi setelah restart
echo     scripts\install\stop.bat  - matikan semua layanan
echo.

:end
pause
endlocal
