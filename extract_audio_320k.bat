@echo off
chcp 65001 >nul
echo ========================================
echo Video Audio Extraction Tool
echo 320k Quality + Adaptive Mode
echo ========================================
echo.
echo Extracting audio with 320k target quality
echo Adaptive quality will automatically adjust if source audio is lower
echo.
echo Starting Python script...
echo.

python extract_audio.py -q 320k --adaptive

echo.
echo Press any key to exit...
pause >nul 