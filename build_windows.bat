@echo off
REM Build a Windows executable using PyInstaller and zip it for release.
REM Usage: run this inside an activated venv that has pyinstaller installed.

:: Ensure we are in repo root
cd /d %~dp0
setlocal EnableDelayedExpansion

:: Create release dir
if not exist release mkdir release

:: Install pyinstaller if missing (best-effort)
python -c "import importlib.util as _iu, sys; sys.exit(0 if _iu.find_spec('PyInstaller') else 2)"
if %errorlevel%==2 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

:: Clean previous builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist moneySmarts.spec del /f moneySmarts.spec

:: Run PyInstaller
pyinstaller --onefile --windowed --name moneySmarts main.py
if errorlevel 1 (
    echo PyInstaller failed. Check the output above.
    pause
    exit /b 1
)

:: Prepare a temporary bundle that will contain only runtime files (exe + assets + minimal docs)
set TMPBUNDLE=%TEMP%\moneySmarts_bundle
if exist "%TMPBUNDLE%" rmdir /s /q "%TMPBUNDLE%"
mkdir "%TMPBUNDLE%"

:: Copy the exe into bundle
if exist dist\moneySmarts.exe (
    copy /y "dist\moneySmarts.exe" "%TMPBUNDLE%\moneySmarts.exe" >nul
) else (
    echo Built executable not found in dist\moneySmarts.exe
    pause
    exit /b 1
)

:: Copy assets excluding developer folders (uses robocopy which exists on most Windows systems)
:: Exclude common dev folders: .git, node_modules, .idea, venv, .venv, tests, build, dist, release
if exist assets (
    robocopy "assets" "%TMPBUNDLE%\assets" /e /xd ".git" "node_modules" ".idea" "venv" ".venv" "tests" "build" "dist" "release" >nul || echo robocopy exit %ERRORLEVEL%
)

:: Also include the moneySmarts config and README so users can tweak settings
mkdir "%TMPBUNDLE%\moneySmarts" 2>nul
if exist moneySmarts\config_default.json copy /y moneySmarts\config_default.json "%TMPBUNDLE%\moneySmarts\config_default.json" >nul 2>&1
if exist README.md copy /y README.md "%TMPBUNDLE%\README.md" >nul 2>&1

:: Optionally include other runtime assets (fonts, ui images) if present in assets they were already copied

:: Create zip from the temporary bundle
set ZIPNAME=release\moneySmarts-windows.zip
if exist "%ZIPNAME%" del /f "%ZIPNAME%" >nul 2>&1
powershell -Command "Compress-Archive -Path '%TMPBUNDLE%\\*' -DestinationPath '%ZIPNAME%' -Force" >nul 2>&1
if exist "%ZIPNAME%" (
    echo Created %ZIPNAME%
) else (
    echo Failed to create %ZIPNAME%
)

:: Cleanup temp bundle
if exist "%TMPBUNDLE%" rmdir /s /q "%TMPBUNDLE%"
echo Done.
pause
