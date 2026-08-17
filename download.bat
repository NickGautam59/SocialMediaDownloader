@echo off

title Facebook Photo Downloader

echo ==========================================
echo Facebook Public Page Photo Downloader
echo ==========================================
echo.

set /p FBURL=Enter Facebook page URL:

echo.
echo Downloading:
echo %FBURL%
echo.

py -m gallery_dl "%FBURL%"

echo.
echo ==========================================
echo Download finished.
echo ==========================================
pause