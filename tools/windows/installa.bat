@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"
title Installazione - Libreria PowerLanguage per MultiCharts

rem ============================================================================
rem  installa.bat - installazione su un PC nuovo della Libreria PowerLanguage
rem
rem  E' l'unico file da scaricare: con un doppio clic controlla che Git e
rem  Python siano presenti (e propone di installarli con winget), scarica la
rem  libreria da GitHub nella cartella scelta, crea l'icona sul desktop e apre
rem  il menu (avvia.bat).
rem
rem  Il repository deve essere raggiungibile: pubblico, oppure con le
rem  credenziali git gia' presenti. Se e' privato, al primo clone Git
rem  Credential Manager apre la finestra di accesso a GitHub: basta fare login
rem  con l'account che ha accesso al repository.
rem
rem  Solo caratteri ASCII in questo file (niente accenti) e fine riga CRLF.
rem  L'espansione ritardata viene attivata solo DOPO aver letto USERPROFILE
rem  (un "!" nel nome utente verrebbe altrimenti mangiato) e viene sospesa
rem  mentre si legge la cartella scelta dall'utente.
rem ============================================================================

set "REPO_URL=https://github.com/tommaso0x/P.git"
set "DEFDEST=%USERPROFILE%\Documents\Libreria-PowerLanguage"
setlocal EnableDelayedExpansion
set "PY="
set "PYVER=-"
set "GITOK=0"

echo ================================================================
echo   Installazione della Libreria PowerLanguage per MultiCharts
echo ================================================================
echo.
echo  Questa procedura:
echo   1. controlla che Git e Python 3 siano installati;
echo   2. scarica la libreria da GitHub nella cartella che scegli;
echo   3. crea l'icona "Libreria PowerLanguage" sul desktop;
echo   4. apre il menu della libreria.
echo.

call :check_tools
if errorlevel 1 exit /b 1

rem ----------------------------------------------------------------------------
rem  Cartella di destinazione
rem ----------------------------------------------------------------------------
echo.
echo  Dove vuoi mettere la libreria? Premi Invio per usare:
echo    !DEFDEST!
rem  Espansione ritardata sospesa: il percorso digitato puo' contenere "!".
rem  (fuori dalle parentesi l'espansione con percento e' sicura, tutto tra virgolette)
setlocal DisableDelayedExpansion
set "DEST="
set /p "DEST=  Cartella: "
if not defined DEST set "DEST=%DEFDEST%"
set "DEST=%DEST:"=%"
if "%DEST:~-1%"=="\" set "DEST=%DEST:~0,-1%"
if not defined DEST set "DEST=%DEFDEST%"
if not "%DEST:!=%"=="%DEST%" (
    echo.
    echo  ERRORE: il percorso contiene un punto esclamativo, che questa procedura
    echo  non gestisce. Scegli una cartella il cui percorso non contenga "!".
    echo.
    pause
    exit /b 1
)
for %%I in ("%DEST%") do set "DEST=%%~fI"
rem  DEST non contiene "!": il valore passa indenne attraverso endlocal.
endlocal & set "DEST=%DEST%"
echo.

if exist "!DEST!\.git" goto :aggiorna

set "NONVUOTA=0"
if exist "!DEST!\" (
    for /f "delims=" %%f in ('dir /a /b "!DEST!" 2^>nul') do set "NONVUOTA=1"
)
if "!NONVUOTA!"=="1" (
    echo  ERRORE: la cartella esiste gia' e non e' una copia della libreria:
    echo    !DEST!
    echo  Scegli un'altra cartella, oppure cancella o rinomina quella esistente.
    echo.
    pause
    exit /b 1
)

echo  Scarico la libreria da GitHub in:
echo    !DEST!
echo.
git clone !REPO_URL! "!DEST!"
if errorlevel 1 (
    echo.
    echo  ERRORE: download non riuscito. Cause frequenti:
    echo   - nessuna connessione a Internet;
    echo   - il repository e' privato e l'account GitHub usato non ha accesso;
    echo   - percorso di destinazione non valido o senza permessi di scrittura.
    echo  Risolvi la causa e riavvia installa.bat.
    echo.
    pause
    exit /b 1
)
goto :completa

:aggiorna
echo  La cartella contiene gia' la libreria: la aggiorno invece di scaricarla di nuovo.
echo    !DEST!
echo.
git -C "!DEST!" pull --ff-only
if errorlevel 1 (
    echo.
    echo  AVVISO: aggiornamento non riuscito. La libreria gia' presente resta
    echo  utilizzabile; potrai riprovare dal menu con la voce 4.
    echo.
)

:completa
if not exist "!DEST!\avvia.bat" (
    echo.
    echo  ERRORE: nella cartella manca avvia.bat. Il download e' incompleto o
    echo  la cartella non e' la libreria giusta.
    echo.
    pause
    exit /b 1
)

echo.
echo  Creo l'icona sul desktop...
call "!DEST!\avvia.bat" icona
if errorlevel 1 (
    echo  AVVISO: icona non creata. Potrai riprovare dal menu con la voce 7.
)
title Installazione - Libreria PowerLanguage per MultiCharts

echo.
echo ================================================================
echo   Installazione completata.
echo ================================================================
echo   Libreria in:  !DEST!
echo   Sul desktop trovi l'icona "Libreria PowerLanguage": un doppio clic
echo   apre il menu. Lo apro adesso in una nuova finestra.
echo.
rem  cmd /c (e non START diretto, che per i .bat usa /K): la finestra si chiude
rem  quando avvia.bat termina, come fa il collegamento sul desktop.
start "" "%ComSpec%" /c ""!DEST!\avvia.bat""
pause
exit /b 0

rem ----------------------------------------------------------------------------
rem  Funzioni di supporto (stessa logica di avvia.bat)
rem ----------------------------------------------------------------------------

:detect_python
set "PY="
set "PYVER=-"
for /f "delims=" %%v in ('py -3 -c "import sys; print(sys.version.split()[0])" 2^>nul') do set "PYVER=%%v"
if "!PYVER:~0,2!"=="3." (
    set "PY=py -3"
    goto :eof
)
set "PYVER=-"
for /f "delims=" %%v in ('python -c "import sys; print(sys.version.split()[0])" 2^>nul') do set "PYVER=%%v"
if "!PYVER:~0,2!"=="3." (
    set "PY=python"
    goto :eof
)
set "PYVER=-"
goto :eof

:check_tools
call :detect_python
set "GITOK=0"
git --version >nul 2>&1
if not errorlevel 1 set "GITOK=1"
if defined PY echo  Python trovato: !PYVER!
if "!GITOK!"=="1" echo  Git trovato.
if defined PY if "!GITOK!"=="1" exit /b 0
echo.
echo  ATTENZIONE: mancano programmi necessari alla libreria.
if not defined PY echo   - Python 3 non trovato. Serve Python 3.10 o superiore.
if "!GITOK!"=="0" echo   - Git non trovato. Serve Git for Windows.
echo.
echo  Si installano con winget (Windows 10/11) con questi comandi:
if not defined PY echo    winget install -e --id Python.Python.3.12
if "!GITOK!"=="0" echo    winget install -e --id Git.Git
echo.
echo  Nota: se installi Python a mano da python.org, spunta "Add python.exe to PATH".
echo  La libreria prova anche "py -3", installato insieme a Python.
echo.
set "RISP=N"
set /p "RISP=  Vuoi eseguire adesso i comandi di installazione? [S/N] "
set "RISP=!RISP:"=!"
if /i not "!RISP:~0,1!"=="S" (
    echo.
    echo  Installa i programmi mancanti e poi riavvia installa.bat.
    echo.
    pause
    exit /b 1
)
call :esegui_winget
echo.
echo  Installazione dei programmi terminata. CHIUDI questa finestra e riavvia
echo  installa.bat: il PATH viene aggiornato solo in una nuova finestra.
echo.
pause
exit /b 1

:esegui_winget
winget --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  winget non e' disponibile su questo PC. Installa a mano:
    echo    Python: https://www.python.org/downloads/windows/  con "Add python.exe to PATH"
    echo    Git:    https://git-scm.com/download/win
    goto :eof
)
if not defined PY (
    echo.
    echo  --- Installazione di Python 3.12 ---
    winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
    if errorlevel 1 echo  AVVISO: winget ha segnalato un errore per Python.
)
if "!GITOK!"=="0" (
    echo.
    echo  --- Installazione di Git ---
    winget install -e --id Git.Git --accept-source-agreements --accept-package-agreements
    if errorlevel 1 echo  AVVISO: winget ha segnalato un errore per Git.
)
goto :eof
