@echo off
setlocal EnableExtensions DisableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"
title Libreria PowerLanguage per MultiCharts

rem ============================================================================
rem  avvia.bat - launcher della Libreria PowerLanguage per MultiCharts
rem
rem  Doppio clic (o icona sul desktop): apre il menu.
rem    avvia.bat icona     : crea/aggiorna solo l'icona sul desktop ed esce
rem    avvia.bat catalogo  : rigenera e apre il catalogo ed esce
rem
rem  Solo caratteri ASCII in questo file (niente accenti) e fine riga CRLF.
rem  Ogni azione del menu termina con "pause" e torna al menu anche in caso
rem  di errore: nessun comando puo' chiudere la finestra all'improvviso.
rem
rem  Il percorso della cartella e l'argomento vengono letti PRIMA di attivare
rem  l'espansione ritardata: cosi' un eventuale "!" nel percorso non viene
rem  mangiato (classica trappola di EnableDelayedExpansion con CD e argomenti).
rem ============================================================================

set "REPO=%CD%"
set "ARG=%~1"
setlocal EnableDelayedExpansion
set "REPO_URL=https://github.com/tommaso0x/P"
set "PY="
set "PYVER=-"
set "GITOK=0"
set "VUOTE=0"

if /i "!ARG!"=="icona" goto :solo_icona
if /i "!ARG!"=="catalogo" goto :solo_catalogo
if defined ARG goto :arg_errato

call :check_tools
if errorlevel 1 exit /b 1
goto :menu

rem ----------------------------------------------------------------------------
rem  Modalita' con argomento
rem ----------------------------------------------------------------------------

:arg_errato
echo  Argomento non riconosciuto: !ARG!
echo  Uso: avvia.bat            apre il menu
echo       avvia.bat icona      crea/aggiorna l'icona sul desktop
echo       avvia.bat catalogo   rigenera e apre il catalogo
pause
exit /b 2

:solo_icona
call :crea_icona
exit /b !errorlevel!

:solo_catalogo
call :check_tools
if errorlevel 1 exit /b 1
call :apri_catalogo
if errorlevel 1 (
    pause
    exit /b 1
)
exit /b 0

rem ----------------------------------------------------------------------------
rem  Menu principale
rem ----------------------------------------------------------------------------

:menu
cls
call :stato_git
echo ================================================================
echo   Libreria PowerLanguage per MultiCharts
echo ================================================================
echo   Cartella:  !REPO!
echo   Ramo:      !BRANCH!
echo   Modifiche non salvate: !DIRTY!
if defined PY (echo   Python:    !PYVER!) else (echo   Python:    NON TROVATO)
if "!GITOK!"=="1" (echo   Git:       ok) else (echo   Git:       NON TROVATO)
echo ----------------------------------------------------------------
echo   1  Apri il catalogo (pagina web locale)
echo   2  Apri la cartella della libreria
echo   3  Nuova voce (procedura guidata)
echo   4  Aggiorna da GitHub (git pull)
echo   5  Salva su GitHub (commit + push)
echo   6  Verifica (test + catalogo)
echo   7  Crea/aggiorna l'icona sul desktop
echo   8  Apri la pagina GitHub del repository
echo   0  Esci
echo ----------------------------------------------------------------
set "SCELTA="
set /p "SCELTA=  Scegli un numero e premi Invio: "
if not defined SCELTA (
    set /a VUOTE+=1
    if !VUOTE! geq 5 goto :fine
    goto :menu
)
set "VUOTE=0"
set "SCELTA=!SCELTA:"=!"
set "AZIONE="
if "!SCELTA!"=="1" set "AZIONE=apri_catalogo"
if "!SCELTA!"=="2" set "AZIONE=apri_cartella"
if "!SCELTA!"=="3" set "AZIONE=nuova_voce"
if "!SCELTA!"=="4" set "AZIONE=aggiorna"
if "!SCELTA!"=="5" set "AZIONE=salva"
if "!SCELTA!"=="6" set "AZIONE=verifica"
if "!SCELTA!"=="7" set "AZIONE=icona"
if "!SCELTA!"=="8" set "AZIONE=github"
if "!SCELTA!"=="0" goto :fine
if not defined AZIONE (
    echo.
    echo  Scelta non valida: !SCELTA!
    echo.
    pause
    goto :menu
)
echo.
call :!AZIONE!
echo.
pause
goto :menu

:fine
echo.
echo  A presto.
endlocal
exit /b 0

rem ----------------------------------------------------------------------------
rem  Azioni del menu (ognuna torna al chiamante con "goto :eof" o "exit /b")
rem ----------------------------------------------------------------------------

:apri_catalogo
if not defined PY goto :no_python
echo  Genero il catalogo e lo apro nel browser...
!PY! tools\render_html.py --open
if errorlevel 1 (
    echo.
    echo  ERRORE: generazione del catalogo non riuscita. Leggi i messaggi qui sopra:
    echo  di solito una scheda ha un metadato non valido. Correggila e riprova.
    exit /b 1
)
exit /b 0

:apri_cartella
echo  Apro la cartella !REPO!
start "" explorer "!REPO!"
goto :eof

:nuova_voce
if not defined PY goto :no_python
!PY! tools\wizard.py
if errorlevel 1 echo  La procedura guidata e' terminata con un errore o e' stata interrotta.
goto :eof

:aggiorna
if "!GITOK!"=="0" goto :no_git
echo  Scarico gli aggiornamenti da GitHub...
git pull --ff-only
if errorlevel 1 (
    echo.
    echo  ERRORE: aggiornamento non riuscito. Cause frequenti:
    echo   - nessuna connessione a Internet, oppure GitHub non raggiungibile;
    echo   - modifiche locali non ancora salvate: usa prima la voce 5;
    echo   - il ramo locale e quello remoto sono divergenti: serve un merge da terminale.
    exit /b 1
)
echo  Aggiornamento completato.
goto :eof

:salva
if "!GITOK!"=="0" goto :no_git
if defined PY (
    echo  Rigenero il catalogo...
    !PY! tools\build_catalog.py
    if errorlevel 1 (
        echo.
        echo  ERRORE: il catalogo non e' valido. Correggi le schede segnalate e riprova.
        exit /b 1
    )
) else (
    echo  AVVISO: Python non trovato, il catalogo non viene rigenerato.
)
git add -A
git diff --cached --quiet
if not errorlevel 1 (
    echo  Nessuna nuova modifica da registrare: controllo che tutto sia su GitHub...
    goto :salva_push
)
echo  Modifiche da salvare:
git status --short
echo.
call :data_oggi
set "DEFMSG=Aggiornamento libreria !OGGI!"
echo  Scrivi il messaggio di commit, oppure premi Invio per usare:
echo    "!DEFMSG!"
set "MSG="
set /p "MSG=  Messaggio: "
if not defined MSG set "MSG=!DEFMSG!"
set "MSG=!MSG:"='!"
call :identita_git
git commit -m "!MSG!"
if errorlevel 1 (
    echo.
    echo  ERRORE: commit non riuscito. Leggi il messaggio qui sopra.
    exit /b 1
)

:salva_push
echo.
echo  Invio a GitHub...
git rev-parse --abbrev-ref --symbolic-full-name @{u} >nul 2>&1
if errorlevel 1 (
    git push -u origin HEAD
) else (
    git push
)
if errorlevel 1 (
    echo.
    echo  ERRORE: push non riuscito. Le modifiche restano salvate in locale:
    echo  riprova piu' tardi con la voce 5.
    echo  Se vedi "Authentication failed", "403" o "Permission denied":
    echo   - il tuo account GitHub non ha accesso in scrittura al repository, oppure
    echo   - Windows ha salvato le credenziali di un altro account GitHub.
    echo  Rimedio: apri "Gestione credenziali" di Windows, sezione "Credenziali Windows",
    echo  elimina la voce git:https://github.com e riprova: Git Credential Manager
    echo  chiedera' di nuovo il login.
    exit /b 1
)
echo  Salvataggio su GitHub completato.
goto :eof

:verifica
if not defined PY goto :no_python
echo  --- Test automatici ---
!PY! -m unittest discover -s tools\tests
if errorlevel 1 (set "ESITO_TEST=FALLITI") else (set "ESITO_TEST=ok")
echo.
echo  --- Controllo del catalogo ---
!PY! tools\build_catalog.py --check
if errorlevel 1 (set "ESITO_CAT=FALLITO") else (set "ESITO_CAT=ok")
echo.
echo  Risultato: test !ESITO_TEST!, catalogo !ESITO_CAT!
if "!ESITO_CAT!"=="FALLITO" echo  Se il catalogo e' solo da rigenerare, la voce 5 lo fa prima di salvare.
goto :eof

:icona
call :crea_icona
goto :eof

:github
echo  Apro !REPO_URL! nel browser...
start "" !REPO_URL!
goto :eof

:no_python
echo  Python non e' disponibile: installa Python 3 (vedi sotto) e riapri il launcher.
echo    winget install -e --id Python.Python.3.12
exit /b 1

:no_git
echo  Git non e' disponibile: installa Git for Windows (vedi sotto) e riapri il launcher.
echo    winget install -e --id Git.Git
exit /b 1

rem ----------------------------------------------------------------------------
rem  Funzioni di supporto
rem ----------------------------------------------------------------------------

:crea_icona
if not exist "tools\windows\crea_collegamento.ps1" (
    echo  ERRORE: manca il file tools\windows\crea_collegamento.ps1
    exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File tools\windows\crea_collegamento.ps1 -Repo "!REPO!"
if errorlevel 1 (
    echo.
    echo  ERRORE: creazione dell'icona non riuscita. Leggi il messaggio qui sopra.
    echo  Prova da PowerShell, nella cartella della libreria:
    echo    powershell -NoProfile -ExecutionPolicy Bypass -File tools\windows\crea_collegamento.ps1
    exit /b 1
)
exit /b 0

:stato_git
set "BRANCH=-"
set "DIRTY=-"
if "!GITOK!"=="0" goto :eof
git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 (
    set "BRANCH=nessuno: la cartella non e' collegata a git"
    goto :eof
)
for /f "delims=" %%b in ('git rev-parse --abbrev-ref HEAD 2^>nul') do set "BRANCH=%%b"
set "DIRTY=no"
for /f "delims=" %%s in ('git status --porcelain 2^>nul') do set "DIRTY=SI"
goto :eof

:data_oggi
set "OGGI="
if defined PY for /f "delims=" %%d in ('!PY! -c "import datetime; print(datetime.date.today().isoformat())" 2^>nul') do set "OGGI=%%d"
if not defined OGGI for /f "delims=" %%d in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd" 2^>nul') do set "OGGI=%%d"
if not defined OGGI set "OGGI=%DATE%"
goto :eof

:identita_git
set "GITNAME="
set "GITMAIL="
for /f "delims=" %%n in ('git config user.name 2^>nul') do set "GITNAME=%%n"
for /f "delims=" %%m in ('git config user.email 2^>nul') do set "GITMAIL=%%m"
if defined GITNAME if defined GITMAIL goto :eof
echo.
echo  Git deve sapere chi firma le modifiche. Viene chiesto una sola volta
echo  e salvato nel profilo utente di Windows.
if not defined GITNAME (
    set /p "GITNAME=  Nome e cognome, oppure il nome utente GitHub: "
    if defined GITNAME git config --global user.name "!GITNAME!"
)
if not defined GITMAIL (
    set /p "GITMAIL=  E-mail, meglio quella dell'account GitHub: "
    if defined GITMAIL git config --global user.email "!GITMAIL!"
)
goto :eof

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
echo  Il launcher prova anche "py -3", installato insieme a Python.
echo.
set "RISP=N"
set /p "RISP=  Vuoi eseguire adesso i comandi di installazione? [S/N] "
set "RISP=!RISP:"=!"
if /i not "!RISP:~0,1!"=="S" (
    echo.
    echo  Va bene. Il menu si apre comunque, ma le voci che richiedono i programmi
    echo  mancanti mostreranno un errore. Installa i programmi e riapri il launcher.
    echo.
    pause
    exit /b 0
)
call :esegui_winget
echo.
echo  Installazione terminata. CHIUDI questa finestra e riapri il launcher:
echo  il PATH viene aggiornato solo in una nuova finestra.
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
