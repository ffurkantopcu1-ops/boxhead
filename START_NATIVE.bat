@echo off
title Boxhead 2.0 (Native Python Evolution)
cd /d "%~dp0"
echo ==========================================
echo   Boxhead 2.0 (Native Python) Baslatiliyor...
echo ==========================================
echo.
echo Bağımlılıklar kontrol ediliyor... (pygame-ce gereklidir)
python -m pip install pygame-ce --quiet

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [UYARI] pygame-ce yüklenirken bir hata oluştu veya Python bulunamadı!
    echo Lütfen Python'un kurulu ve PATH'e ekli olduğundan emin olun.
    pause
    exit /b
)

echo.
echo Oyun Başlatılıyor...
python main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [HATA] Oyun beklenmedik bir şekilde kapandı.
    pause
)
