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
echo   ^| . \   / ___ \   ^| ^|        haelt den PC bei kurzer
echo   ^|_^|\_\ /_/   \_\  ^|_^|        Abwesenheit wach.
echo   ============================================================
echo.
echo    Nur zu Forschungs- und Demonstrationszwecken.
echo.

set "KAT_DL=%~dp0"
set "KAT_TARGET=%USERPROFILE%\.tracehost"
set "KAT_SCRIPT=%KAT_TARGET%\kat.pyw"
set "KAT_PYW="

REM Programm-Ordner finden (der Unterordner mit kat.pyw) - Name egal (Umlaut/Leerzeichen)
set "KAT_PAYLOAD="
for /d %%D in ("%KAT_DL%*") do if not defined KAT_PAYLOAD if exist "%%~D\kat.pyw" set "KAT_PAYLOAD=%%~D"
if not defined KAT_PAYLOAD if exist "%KAT_DL%kat.pyw" set "KAT_PAYLOAD=%KAT_DL:~0,-1%"

if not defined KAT_PAYLOAD (
  echo   [!] Die Programmdateien wurden nicht gefunden.
  echo       Bitte den heruntergeladenen ZIP-Ordner ZUERST komplett ENTPACKEN
  echo       und install.bat aus dem entpackten Ordner starten
  echo       ^(nicht direkt aus der ZIP-Vorschau doppelklicken^).
  echo.
  echo   Wenn nichts klappt, bitte bei Ollio melden!
  echo.
  pause
  exit /b 1
)

echo   [1/5] Python-Launcher suchen...
call :resolve
if not defined KAT_PYW (
  echo         nicht gefunden - installiere Python einmalig ^(kann etwas dauern^)...
  where winget >nul 2>&1
  if errorlevel 1 (
    echo.
    echo   [!] Python fehlt und winget ist nicht verfuegbar.
    echo       Bitte Python installieren: https://www.python.org/downloads/
    echo       ^("Add python.exe to PATH" anhaken^), dann install.bat erneut starten.
    echo.
    echo   Wenn nichts klappt, bitte bei Ollio melden!
    echo.
    pause
    exit /b 1
  )
  winget install -e --id Python.Python.3.12 --silent --accept-source-agreements --accept-package-agreements
  call :resolve
)
if not defined KAT_PYW (
  echo.
  echo   [!] Python-Launcher nach der Installation nicht gefunden.
  echo       Bitte den PC neu starten und install.bat erneut ausfuehren.
  echo.
  echo   Wenn nichts klappt, bitte bei Ollio melden!
  echo.
  pause
  exit /b 1
)
echo         OK: %KAT_PYW%

echo   [2/5] Dateien installieren...
if not exist "%KAT_TARGET%" mkdir "%KAT_TARGET%"
copy /y "%KAT_PAYLOAD%\kat.pyw" "%KAT_TARGET%\kat.pyw" >nul
if exist "%KAT_PAYLOAD%\kat.ico"      copy /y "%KAT_PAYLOAD%\kat.ico"      "%KAT_TARGET%\kat.ico"      >nul
if exist "%KAT_PAYLOAD%\make_icon.py" copy /y "%KAT_PAYLOAD%\make_icon.py" "%KAT_TARGET%\make_icon.py" >nul
attrib +h "%KAT_TARGET%" >nul 2>&1
if not exist "%KAT_TARGET%\kat.ico" if exist "%KAT_TARGET%\make_icon.py" "%KAT_PYW%" "%KAT_TARGET%\make_icon.py" >nul 2>&1
if not exist "%KAT_TARGET%\kat.pyw" (
  echo.
  echo   [!] Kopieren fehlgeschlagen. Bitte den ZIP-Ordner entpacken und
  echo       install.bat erneut ausfuehren.
  echo.
  echo   Wenn nichts klappt, bitte bei Ollio melden!
  echo.
  pause
  exit /b 1
)
echo         OK: %KAT_TARGET%

echo   [3/5] Getarnte Desktop-Verknuepfung anlegen...
powershell -NoProfile -Command "$w=New-Object -ComObject WScript.Shell; $d=[Environment]::GetFolderPath('Desktop'); $p=(Join-Path $d 'tracertStray.lnk'); $s=$w.CreateShortcut($p); $s.TargetPath=$env:KAT_PYW; $s.Arguments=[char]34+$env:KAT_SCRIPT+[char]34; $s.WorkingDirectory=$env:KAT_TARGET; $s.IconLocation=$env:SystemRoot+'\System32\imageres.dll,109'; $s.Description='trace host'; $s.Save(); Write-Host ('        OK: '+$p)"

echo   [4/5] Starten...
start "" "%KAT_PYW%" "%KAT_SCRIPT%"
echo         OK

echo   [5/5] Fertig.
echo.
echo   ============================================================
echo      KAT installiert.
echo      Verknuepfung am Desktop getarnt unter dem Namen:
echo.
echo            tracertStray
echo.
echo   ------------------------------------------------------------
echo    Steuern: kleines Icon unten rechts unter dem Pfeil ^(^) neben
echo    der Uhr - Rechtsklick -^> Jetzt testen / Beenden.
echo.
echo    Hinweis: Dieser heruntergeladene Ordner wird jetzt versucht
echo    automatisch zu loeschen. Falls etwas uebrig bleibt, bitte
echo    den Ordner einfach selbst loeschen - nur die Desktop-
echo    Verknuepfung wird gebraucht.
echo.
echo    Nur zu Forschungszwecken. Wenn nichts klappt: bei Ollio melden!
echo   ============================================================
echo.
echo   Zum Schliessen eine Taste druecken...
pause >nul

REM Selbst-Aufraeumen des Download-Ordners (nur wenn es wirklich der Download ist)
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
