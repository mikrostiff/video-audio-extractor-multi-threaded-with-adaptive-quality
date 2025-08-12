@echo off
chcp 65001 >nul
echo ========================================
echo Video Audio Extraction Tool
echo Standard Version + Resume + Parallel + Adaptive Quality
echo ========================================
echo.
echo This version supports multiple audio formats
echo Resume from interruption and parallel processing
echo Adaptive quality based on source video audio bitrate
echo Default reads from ./original folder
echo Auto-uses multi-process for speed boost
echo.
echo Quality options:
echo   -q 64k   : Low quality (64 kbps)
echo   -q 128k  : Standard quality (128 kbps) 
echo   -q 192k  : High quality (192 kbps) - DEFAULT
echo   -q 256k  : Very high quality (256 kbps)
echo   -q 320k  : Maximum quality (320 kbps)
echo.
echo Starting Python script with adaptive quality...
echo.

python extract_audio.py --adaptive

echo.
echo Press any key to exit...
pause >nul 