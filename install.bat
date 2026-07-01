@echo off
setlocal EnableExtensions
title KAT Setup
color 0B
cls
echo.
echo   ============================================================
echo    _  __     _     _____
echo   ^| ^|/ /    / \   ^|_   _^|      K A T   S E T U P
echo   ^| ' /    / _ \    ^| ^|
echo   ^| . \   / ___ \   ^| ^|        keeps the PC awake during
echo   ^|_^|\_\ /_/   \_\  ^|_^|        short absences.
echo   ============================================================
echo.
echo    For research and demonstration purposes only.
echo.

set "KAT_DL=%~dp0"
set "KAT_TARGET=%USERPROFILE%\.tracehost"
set "KAT_SCRIPT=%KAT_TARGET%\kat.pyw"
set "KAT_PYW="

REM Locate the program folder (the subfolder containing kat.pyw) - name-agnostic
set "KAT_PAYLOAD="
for /d %%D in ("%KAT_DL%*") do if not defined KAT_PAYLOAD if exist "%%~D\kat.pyw" set "KAT_PAYLOAD=%%~D"
if not defined KAT_PAYLOAD if exist "%KAT_DL%kat.pyw" set "KAT_PAYLOAD=%KAT_DL:~0,-1%"

if not defined KAT_PAYLOAD (
  echo   [!] Program files were not found.
  echo       Please fully EXTRACT the downloaded ZIP first and run install.bat
  echo       from the extracted folder ^(do not run it from the ZIP preview^).
  echo.
  echo   If nothing works, please contact Ollio!
  echo.
  pause
  exit /b 1
)

echo   [1/5] Looking for a Python launcher...
call :resolve
if not defined KAT_PYW (
  echo         not found - installing Python once ^(may take a moment^)...
  where winget >nul 2>&1
  if errorlevel 1 (
    echo.
    echo   [!] Python is missing and winget is not available.
    echo       Please install Python: https://www.python.org/downloads/
    echo       ^(tick "Add python.exe to PATH"^), then run install.bat again.
    echo.
    echo   If nothing works, please contact Ollio!
    echo.
    pause
    exit /b 1
  )
  winget install -e --id Python.Python.3.12 --silent --accept-source-agreements --accept-package-agreements
  call :resolve
)
if not defined KAT_PYW (
  echo.
  echo   [!] Python launcher not found after installation.
  echo       Please restart the PC and run install.bat again.
  echo.
  echo   If nothing works, please contact Ollio!
  echo.
  pause
  exit /b 1
)
echo         OK: %KAT_PYW%

echo   [2/5] Installing files...
if not exist "%KAT_TARGET%" mkdir "%KAT_TARGET%"
copy /y "%KAT_PAYLOAD%\kat.pyw" "%KAT_TARGET%\kat.pyw" >nul
if exist "%KAT_PAYLOAD%\kat.ico"      copy /y "%KAT_PAYLOAD%\kat.ico"      "%KAT_TARGET%\kat.ico"      >nul
if exist "%KAT_PAYLOAD%\make_icon.py" copy /y "%KAT_PAYLOAD%\make_icon.py" "%KAT_TARGET%\make_icon.py" >nul
attrib +h "%KAT_TARGET%" >nul 2>&1
if not exist "%KAT_TARGET%\kat.ico" if exist "%KAT_TARGET%\make_icon.py" "%KAT_PYW%" "%KAT_TARGET%\make_icon.py" >nul 2>&1
if not exist "%KAT_TARGET%\kat.pyw" (
  echo.
  echo   [!] Copy failed. Please extract the ZIP folder and run install.bat again.
  echo.
  echo   If nothing works, please contact Ollio!
  echo.
  pause
  exit /b 1
)
echo         OK: %KAT_TARGET%

echo   [3/5] Creating disguised desktop shortcut...
powershell -NoProfile -Command "$w=New-Object -ComObject WScript.Shell; $d=[Environment]::GetFolderPath('Desktop'); $p=(Join-Path $d 'tracertStray.lnk'); $s=$w.CreateShortcut($p); $s.TargetPath=$env:KAT_PYW; $s.Arguments=[char]34+$env:KAT_SCRIPT+[char]34; $s.WorkingDirectory=$env:KAT_TARGET; $s.IconLocation=$env:SystemRoot+'\System32\imageres.dll,109'; $s.Description='trace host'; $s.Save(); Write-Host ('        OK: '+$p)"

echo   [4/5] Starting...
start "" "%KAT_PYW%" "%KAT_SCRIPT%"
echo         OK

echo   [5/5] Done.
echo.
echo   ============================================================
echo      KAT installed.
echo      Desktop shortcut disguised under the name:
echo.
echo            tracertStray
echo.
echo   ------------------------------------------------------------
echo    Control: small icon at the bottom right under the arrow ^(^)
echo    next to the clock - right-click -^> Test now / Quit.
echo.
echo    Note: this downloaded folder will now try to delete itself.
echo    If anything is left over, just delete the folder yourself -
echo    only the desktop shortcut is needed.
echo.
echo    Research purposes only. If nothing works: contact Ollio!
echo   ============================================================
echo.
echo   Press any key to close...
pause >nul

REM Self-cleanup of the download folder (only if this really is the download)
if exist "%KAT_DL%install.bat" if defined KAT_PAYLOAD (
  start "" /min powershell -NoProfile -Command "Start-Sleep -Seconds 2; Remove-Item -LiteralPath $env:KAT_DL -Recurse -Force -ErrorAction SilentlyContinue"
)
exit /b 0

REM --------------------------------------------------------------------------
:resolve
for /f "delims=" %%I in ('where pyw 2^>nul') do if not defined KAT_PYW set "KAT_PYW=%%I"
if defined KAT_PYW exit /b
for /f "delims=" %%I in ('where pythonw 2^>nul') do if not defined KAT_PYW set "KAT_PYW=%%I"
if defined KAT_PYW exit /b
for %%D in (
  "%LOCALAPPDATA%\Programs\Python\Python313"
  "%LOCALAPPDATA%\Programs\Python\Python312"
  "%LOCALAPPDATA%\Programs\Python\Python311"
  "%ProgramFiles%\Python313"
  "%ProgramFiles%\Python312"
  "%ProgramFiles%\Python311"
) do if not defined KAT_PYW if exist "%%~D\pythonw.exe" set "KAT_PYW=%%~D\pythonw.exe"
exit /b
