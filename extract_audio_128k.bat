@echo off
chcp 65001 >nul
echo ========================================
echo Video Audio Extraction Tool
echo 128k Quality + Adaptive Mode
echo ========================================
echo.
echo Extracting audio with 128k target quality
echo Adaptive quality will automatically adjust if source audio is lower
echo.
echo Starting Python script...
echo.

python extract_audio.py -q 128k --adaptive

echo.
echo Press any key to exit...
pause >nul 