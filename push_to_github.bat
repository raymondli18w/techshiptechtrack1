@echo off
chcp 65001 >nul
cd /d "C:\Users\RaymondLi\OneDrive - 18wheels.ca\downloads may 30 2023\test6\2026\feb 2026 1"

echo ========================================
echo TECHSHIP HOURLY SYNC - %date% %time%
echo ========================================
echo.

:: Step 1: Fetch fresh data from TechShip APIs
echo [1/4] Fetching fresh TechShip data...
python fetch_techship_parcel_with_tracking_FINAL_FIXED.py
if errorlevel 1 (
    echo ❌ Fetch failed - aborting sync
    timeout /t 10
    exit /b 1
)

:: Step 2: Update master database
echo.
echo [2/4] Updating master database...
cd techship_system
python update_master.py
if errorlevel 1 (
    echo ❌ Update failed - aborting sync
    timeout /t 10
    exit /b 1
)

:: Step 3: TRIM to 30,000 newest rows (critical for GitHub safety)
echo.
echo [3/4] Trimming to 30,000 newest rows (by ProcessedOn)...
python trim_master.py
if errorlevel 1 (
    echo ❌ Trim failed - aborting sync
    timeout /t 10
    exit /b 1
)

:: Step 4: Push trimmed file to GitHub
echo.
echo [4/4] Pushing to GitHub...
git add master_database.xlsx
git commit -m "auto: hourly sync %date% %time%" --allow-empty
git push origin main
if errorlevel 1 (
    echo ⚠️ Push failed - check git status
    git status
    timeout /t 10
    exit /b 1
)

echo.
echo ========================================
echo ✅ SYNC COMPLETE
echo    - 30,000 newest rows preserved
echo    - Oldest rows auto-trimmed
echo    - Safe for GitHub (42 MB target)
echo ========================================
timeout /t 5