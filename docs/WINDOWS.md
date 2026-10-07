# Avvio a un clic su Windows

Come installare la libreria su un PC Windows e usarla **senza terminale**: un'icona sul desktop apre
il menu di `avvia.bat`, che genera e apre il catalogo come pagina web (con il pulsante "Copia
codice"), guida la creazione di nuove voci, aggiorna e salva su GitHub, esegue la verifica. Le
convenzioni della libreria sono in [CONVENZIONI.md](CONVENZIONI.md), il flusso di lavoro in
[WORKFLOW.md](WORKFLOW.md), le operazioni nel PowerLanguage Editor in
[MULTICHARTS.md](MULTICHARTS.md); l'uso da terminale è nel
[README](../README.md#avvio-rapido-da-terminale).

## Prerequisiti

| Cosa | A cosa serve | Come averlo |
|---|---|---|
| **Windows 10 o 11** | `avvia.bat` usa `cmd.exe`, PowerShell e, per installare ciò che manca, `winget` | — |
| **Git for Windows** | scaricare e aggiornare la libreria, salvare su GitHub; include **Git Credential Manager** per il login a GitHub | `winget install -e --id Git.Git` oppure <https://git-scm.com/download/win> |
| **Python 3.10 o successivo** | catalogo (`render_html.py`, `build_catalog.py`), procedura guidata (`wizard.py`), test | `winget install -e --id Python.Python.3.12` oppure <https://www.python.org/downloads/windows/>; nell'installer di python.org spuntare **"Add python.exe to PATH"** |
| Un account GitHub con accesso al repository | solo per scaricare un repository privato e per salvare le modifiche | — |

`installa.bat` e `avvia.bat` controllano da soli che Git e Python ci siano: se mancano, spiegano
cosa manca, mostrano i due comandi `winget` qui sopra e chiedono (`S/N`) se eseguirli subito. Dopo
l'installazione bisogna **chiudere e riaprire** il launcher: il `PATH` aggiornato si vede solo in
una finestra nuova. Non serve nient'altro: nessun pacchetto Python da installare (tutto usa la
libreria standard), nessun programma oltre a Git e Python.

## Prima installazione, passo per passo

1. Scaricare **un solo file**, `tools/windows/installa.bat`, da
   <https://raw.githubusercontent.com/tommaso0x/P/claude/powerlanguage-library-indicators-brr3a5/tools/windows/installa.bat>
   (nel browser: tasto destro → *Salva con nome*; lasciare il nome `installa.bat` e, se il browser
   lo salva come `installa.bat.txt`, correggerlo). La parte
   `claude/powerlanguage-library-indicators-brr3a5` dell'indirizzo è il **nome del ramo**: se il
   ramo viene rinominato o unito in `main`, va sostituita con il nome nuovo. Lo stesso file si
   raggiunge dalla pagina GitHub del repository aprendo `tools/windows/installa.bat` e scegliendo
   *Raw*.
2. **Doppio clic su `installa.bat`.** Se compare "PC protetto da Windows" (SmartScreen), scegliere
   *Ulteriori informazioni* → *Esegui comunque*: succede con qualunque `.bat` scaricato da Internet
   (vedi [Problemi frequenti](#problemi-frequenti)).
3. La finestra controlla **Git e Python**. Se mancano, mostra i comandi `winget` e chiede se
   eseguirli; al termine chiudere la finestra e **riaprire `installa.bat`**.
4. Chiede la **cartella di destinazione**. Invio accetta
   `%USERPROFILE%\Documents\Libreria-PowerLanguage` (cioè `Documenti\Libreria-PowerLanguage`);
   si può scrivere un altro percorso. Se la cartella esiste già e contiene la libreria (c'è `.git`),
   viene **aggiornata** con `git pull --ff-only` invece di essere scaricata di nuovo; se esiste, non
   è vuota e non è la libreria, la procedura si ferma con un messaggio chiaro: scegliere un'altra
   cartella. Il percorso può contenere spazi, ma non il punto esclamativo (`!`): in quel caso
   `installa.bat` si ferma e chiede un'altra cartella.
5. Scarica la libreria con `git clone https://github.com/tommaso0x/P.git "<cartella>"` (il ramo
   predefinito del repository, senza nomi di ramo fissati nello script). Se il repository è
   **privato**, Git Credential Manager apre la finestra di accesso a GitHub: accedere con l'account
   che ha accesso; le credenziali restano salvate in Windows e non vengono più chieste.
6. Crea l'icona **"Libreria PowerLanguage"** sul desktop (`avvia.bat icona`) e apre il menu in una
   nuova finestra (`avvia.bat`). L'installazione è finita: da qui in avanti basta l'icona.

Chi ha già clonato il repository (per esempio con `git clone https://github.com/tommaso0x/P.git`)
salta `installa.bat`: doppio clic su `avvia.bat` nella cartella clonata e, dal menu, voce `7` per
l'icona.

## Il menu di avvia.bat

Doppio clic sull'icona (o su `avvia.bat`). All'avvio la finestra mostra la **cartella** della
libreria, il **ramo** git corrente, se ci sono **modifiche non salvate** (`git status --porcelain`),
la versione di **Python** trovata e se **Git** è disponibile. Poi il menu:

```
  1  Apri il catalogo (pagina web locale)
  2  Apri la cartella della libreria
  3  Nuova voce (procedura guidata)
  4  Aggiorna da GitHub (git pull)
  5  Salva su GitHub (commit + push)
  6  Verifica (test + catalogo)
  7  Crea/aggiorna l'icona sul desktop
  8  Apri la pagina GitHub del repository
  0  Esci
```

| Voce | Cosa fa esattamente |
|---|---|
| `1` Apri il catalogo (pagina web locale) | `python tools\render_html.py --open`: valida le schede, rigenera `CATALOG.md` e `catalog.json` se non sono aggiornati, scrive `catalog.html` nella radice della libreria e lo apre nel browser predefinito. Se una scheda non è valida stampa gli `ERRORE <percorso>: <messaggio>` e non scrive nulla. Vedi [Il catalogo come pagina web](#il-catalogo-come-pagina-web). |
| `2` Apri la cartella della libreria | apre la cartella della libreria in Esplora file. |
| `3` Nuova voce (procedura guidata) | `python tools\wizard.py`: domande in italiano una alla volta, poi crea la voce chiamando `new_entry.py`. Vedi [La procedura guidata](#la-procedura-guidata). |
| `4` Aggiorna da GitHub (git pull) | `git pull --ff-only` e stampa il risultato. Se fallisce spiega le cause frequenti: nessuna connessione, modifiche locali non ancora salvate (usare prima la voce `5`), ramo locale e remoto divergenti (serve un merge da terminale). |
| `5` Salva su GitHub (commit + push) | rigenera il catalogo con `build_catalog.py` (si ferma se le schede non sono valide); `git add -A`; se non c'è nulla da registrare lo dice e passa direttamente al push; altrimenti mostra i file modificati, chiede il **messaggio di commit** (Invio = `Aggiornamento libreria <data>`), se `git config user.name` o `user.email` sono vuoti chiede nome ed e-mail e li salva con `--global`, poi `git commit` e `git push` (`git push -u origin HEAD` la prima volta che il ramo viene inviato). Gli errori di autenticazione e 403 sono spiegati in italiano: vedi [Accesso a GitHub](#accesso-a-github). |
| `6` Verifica (test + catalogo) | `python -m unittest discover -s tools\tests` e poi `python tools\build_catalog.py --check`: lo stesso controllo che fa la CI. Riporta l'esito di entrambi; se il catalogo è solo da rigenerare, lo fa la voce `5` prima di salvare. |
| `7` Crea/aggiorna l'icona sul desktop | `powershell -NoProfile -ExecutionPolicy Bypass -File tools\windows\crea_collegamento.ps1 -Repo "<cartella>"`. Vedi [L'icona sul desktop](#licona-sul-desktop). |
| `8` Apri la pagina GitHub del repository | apre <https://github.com/tommaso0x/P> nel browser. |
| `0` Esci | chiude la finestra. |

Ogni voce termina con *Premere un tasto per continuare* (`pause`), così l'esito si legge con calma
prima di tornare al menu. Se Python o Git mancano, le voci che li richiedono lo dicono e rimandano
ai comandi `winget`.

`avvia.bat` accetta anche un argomento, comodo per altri collegamenti o per automatizzare:

| Comando | Effetto |
|---|---|
| `avvia.bat` | menu |
| `avvia.bat catalogo` | rigenera e apre il catalogo, poi esce (la voce `1` senza menu) |
| `avvia.bat icona` | crea/aggiorna solo l'icona sul desktop, poi esce (la voce `7` senza menu) |

## Dove sta la libreria

Nella cartella scelta durante l'installazione (default `Documenti\Libreria-PowerLanguage`). È un
normale clone git del repository: `avvia.bat` nella radice, le voci in `indicators/`, `strategies/`,
`functions/` e `papers/`, il catalogo (`CATALOG.md`, `catalog.json`) e la pagina `catalog.html`
generata localmente. La voce `2` del menu la apre in Esplora file; il percorso compare anche nella
prima riga del menu.

Due cose restano solo in locale e non vanno su GitHub (sono in `.gitignore`): `catalog.html` e i
collegamenti `*.lnk`.

## L'icona sul desktop

L'icona è un normale **collegamento** di Windows, `Libreria PowerLanguage.lnk`, creato sul desktop
da `tools/windows/crea_collegamento.ps1` (richiamato da `installa.bat`, dalla voce `7` del menu e da
`avvia.bat icona`). Il collegamento:

- punta a `cmd.exe` (`%ComSpec%`) con argomenti `/c ""<cartella>\avvia.bat""` (le doppie
  virgolette servono per i percorsi con spazi);
- ha come cartella di lavoro la cartella della libreria;
- usa l'immagine `tools\windows\libreria.ico` (se il file manca, un'icona di sistema di
  `shell32.dll`);
- viene scritto nel desktop restituito da `[Environment]::GetFolderPath('Desktop')`, quindi finisce
  nel posto giusto anche quando il desktop è spostato su **OneDrive**.

`libreria.ico` è generato da `tools/windows/make_icon.py` (solo libreria standard, output
riproducibile): un quadrato blu scuro ad angoli arrotondati con una spezzata ascendente e piccole
candele, leggibile anche a 16-32 px, in quattro dimensioni (16, 32, 48 e 256 px) salvate come PNG
dentro il file ICO. Si rigenera con `python tools\windows\make_icon.py`.

Lo script del collegamento si può lanciare anche a mano:

```bat
powershell -NoProfile -ExecutionPolicy Bypass -File tools\windows\crea_collegamento.ps1 -Repo "C:\percorso\della\libreria"
```

Senza `-Repo` usa la cartella padre di `tools\windows\`, cioè la radice della libreria. Al termine
stampa il percorso del collegamento creato.

### Spostare o rinominare la cartella

Il collegamento contiene il percorso assoluto della cartella: dopo averla spostata o rinominata
l'icona non funziona più. Rimedio: nella nuova posizione doppio clic su `avvia.bat` e voce `7`
(oppure `avvia.bat icona`): il collegamento viene riscritto con il percorso nuovo. Nulla altro
dipende dal percorso.

## Accesso a GitHub

- Tutto passa per **HTTPS** (`https://github.com/tommaso0x/P.git`): nessuna chiave SSH da
  configurare.
- **Login.** Git for Windows include **Git Credential Manager**: al primo `git clone` di un
  repository privato e al primo `git push` apre una finestra per accedere a GitHub (nel browser o
  con un codice); le credenziali restano salvate in *Gestione credenziali* di Windows e non vengono
  più chieste.
- **Chi firma i commit.** La prima volta che si usa la voce `5`, se `git config user.name` o
  `user.email` sono vuoti, il menu chiede nome ed e-mail (meglio quella dell'account GitHub) e li
  salva con `--global`, cioè per tutti i repository dell'utente di Windows.
- **Errore `403`, "Authentication failed" o "Permission denied" al push.** L'account con cui Windows
  si presenta a GitHub non ha i diritti di scrittura sul repository, oppure Windows ha salvato la
  credenziale di un altro account. Le modifiche restano comunque salvate in locale. Rimedio: aprire
  *Gestione credenziali* → *Credenziali Windows*, eliminare la voce `git:https://github.com`,
  ripetere la voce `5`: Git Credential Manager chiede di nuovo il login. Se il problema resta,
  l'account usato non è collaboratore del repository.
- Un repository **pubblico** si scarica senza login; il login serve comunque per salvare.

## Aggiornare

- **La libreria**: voce `4 Aggiorna da GitHub (git pull)`, cioè `git pull --ff-only`. Se ci sono
  modifiche locali non ancora salvate, prima la voce `5`. Anche rilanciare `installa.bat` indicando
  la stessa cartella aggiorna la libreria (riconosce `.git` e fa il pull invece del clone).
- **Il catalogo**: lo rigenerano la voce `1` (compreso `catalog.html`) e la voce `5` (prima del
  commit); la voce `6` controlla che sia valido e aggiornato.
- **Git e Python**: `winget upgrade --id Git.Git` e `winget upgrade --id Python.Python.3.12`, oppure
  gli installer dei rispettivi siti. Poi riaprire il launcher.

## Il catalogo come pagina web

`catalog.html` (voce `1`, `avvia.bat catalogo` oppure `python tools\render_html.py --open`) è una
sola pagina autosufficiente: CSS e JavaScript inline, nessuna risorsa esterna, si apre dal disco
(`file://`), è in italiano, chiara o scura secondo le impostazioni di Windows, leggibile anche da
telefono. Contiene:

- l'**intestazione** con titolo, conteggi, la **casella di ricerca** (filtra le schede per testo) e
  i **tag** cliccabili che filtrano;
- le sezioni **Indicatori**, **Strategie**, **Funzioni**, **Fonti**;
- per ogni voce di codice: nome, tipo, stato, versione, linguaggio se diverso da PowerLanguage,
  sintesi, tag, **Fonti** e **Dipendenze** (link interni alla pagina) e i pulsanti **Copia codice**
  (copia tutto il testo del `.pl` negli appunti e conferma con "Copiato!"), **Mostra codice**
  (mostra/nasconde il sorgente), **Scheda** (mostra/nasconde la `README.md` resa in HTML),
  **Apri cartella** e **Apri .pl** (link relativi alla cartella della voce);
- per ogni fonte: titolo, autori, anno, tipo, stato, rivista/volume/numero/pagine quando presenti,
  link **DOI**/**URL** (si aprono in una nuova scheda del browser), tag, **Implementazioni** (link
  interni), **Scheda**, link a `notes.md` e al PDF se presenti.

Il modo più rapido per portare uno studio in MultiCharts: voce `1`, cercare la voce, **Copia
codice**, poi nel PowerLanguage Editor `File > New > ...` e Ctrl+V (dettagli in
[MULTICHARTS.md](MULTICHARTS.md#creare-uno-studio-da-un-file-pl)). Il pulsante usa gli appunti del
browser (`navigator.clipboard`) e, se il browser non lo consente da `file://`, ricade su una copia
classica; in entrambi i casi compare "Copiato!".

La pagina è **generata e locale**: non si modifica a mano (le modifiche si fanno nelle schede e si
rigenera), non è versionata (`.gitignore`) e `build_catalog.py --check` non la considera. Da
terminale: `python tools/render_html.py [--root <path>] [--out catalog.html] [--open] [--quiet] [--no-catalog]`
(`--stamp` aggiunge la riga "Generato il ..."; senza, l'output è deterministico; `--no-catalog` non
rigenera `CATALOG.md`/`catalog.json`).

## La procedura guidata

Voce `3`, oppure `python tools\wizard.py` (`--root <path>` per un'altra radice, `--dry-run` per una
prova senza scrivere nulla, `--date AAAA-MM-GG` per una data diversa da oggi). L'aiuto `--help` di
tutti gli strumenti è in italiano, salvo le righe fisse `usage:` e `options:` che Python genera in
inglese. Chiede, una cosa alla volta e in italiano:

1. il **tipo** di voce: `1` indicatore, `2` strategia, `3` funzione, `4` fonte;
2. il **nome** dello studio (o il titolo della fonte); un nome vuoto viene richiesto; per le
   **funzioni** il nome deve essere un identificatore PowerLanguage valido (lettere, cifre e `_`,
   non può iniziare con una cifra), altrimenti viene rifiutato e richiesto;
3. per le voci di codice: le **fonti**, scelte dall'elenco numerato delle fonti già presenti (più
   numeri separati da virgola, Invio per nessuna, oppure un nuovo id scritto a mano); le
   **dipendenze**, dall'elenco numerato delle funzioni esistenti; i **tag** (separati da virgola; i
   tag già in uso sono mostrati come suggerimento); la **sintesi** in una riga;
4. per le fonti: autori, anno, tipo (`paper`, `book`, `chapter`, `article`, `thesis`, `web`), DOI,
   URL, tag, sintesi.

Propone lo slug (subito dopo il nome) o l'id (dopo tag e sintesi) derivato, da accettare con Invio
o modificare, mostra il comando `new_entry.py` esatto che eseguirà, chiede conferma e crea la voce (chiamando `new_entry.py` nello stesso processo). Al termine elenca i file
creati e i passi successivi (compilare la scheda, incollare il codice nel `.pl`, eseguire la voce
`6 Verifica` del menu) e propone di aprire la cartella in Esplora file. Ctrl+C in qualunque momento
annulla con un messaggio, senza lasciare nulla a metà. Le stesse cose si ottengono da terminale
con i flag di `new_entry.py` ([WORKFLOW.md](WORKFLOW.md)).

## Problemi frequenti

**"Python: NON TROVATO" anche se Python è installato.** Windows 10/11 contengono un finto
`python.exe` (un *alias di esecuzione app*) che apre il Microsoft Store invece di eseguire Python;
`avvia.bat` lo riconosce (non stampa una versione `3.x`) e lo ignora. Rimedi: installare Python da
python.org **con "Add python.exe to PATH" spuntato**, oppure con
`winget install -e --id Python.Python.3.12`; se Python è installato ma non in `PATH`, disattivare
gli alias in
*Impostazioni → App → Impostazioni avanzate dell'app → Alias di esecuzione app* (su Windows 10:
*App → App e funzionalità → Alias di esecuzione app*) (`python.exe`, `python3.exe`) oppure reinstallare spuntando l'opzione del `PATH`. Il launcher prova prima `py -3`
(il *Python Launcher for Windows* installato da python.org) e poi `python`. Dopo ogni installazione
chiudere e riaprire il launcher.

**"Git: NON TROVATO".** Installare Git for Windows (`winget install -e --id Git.Git`) lasciando
l'opzione predefinita *Git from the command line and also from 3rd-party software*, poi riaprire il
launcher.

**L'icona non viene creata (PowerShell).** `avvia.bat` chiama PowerShell con
`-NoProfile -ExecutionPolicy Bypass`, quindi i criteri di esecuzione normali non servono né vanno
cambiati. Se
un criterio aziendale blocca comunque gli script ("l'esecuzione di script è disabilitata nel
sistema"), creare il collegamento a mano: tasto destro sul desktop → *Nuovo* → *Collegamento*,
percorso `cmd.exe /c ""C:\percorso\della\libreria\avvia.bat""`, nome `Libreria PowerLanguage`; poi
*Proprietà* → *Da:* la cartella della libreria, *Cambia icona* → `tools\windows\libreria.ico`.

**Desktop su OneDrive.** Il collegamento viene creato nel desktop effettivo (anche se spostato su
OneDrive). Se OneDrive sincronizza il desktop su un altro PC, lì il collegamento non funziona
(contiene il percorso di questo PC): ricrearlo su quel PC con la voce `7`. Se anche la cartella
`Documenti` è sincronizzata da OneDrive, la libreria funziona ugualmente, ma OneDrive e git possono
ostacolarsi (file bloccati, copie "in conflitto"): in caso di problemi reinstallare scegliendo una
cartella fuori da OneDrive, per esempio `C:\Libreria-PowerLanguage`, e ricreare l'icona.

**Antivirus, SmartScreen e file `.bat`.** Un `.bat` scaricato da Internet porta il "marchio del
web": Windows mostra "PC protetto da Windows" (*Ulteriori informazioni* → *Esegui comunque*) oppure
il browser avverte che il file "potrebbe essere pericoloso" (*Mantieni*). In alternativa: tasto
destro sul file → *Proprietà* → *Annulla blocco*. Qualche antivirus mette in quarantena gli script
`.bat`: aggiungere la cartella della libreria alle esclusioni. Gli script sono leggibili con
qualunque editor di testo: contengono solo i comandi descritti in questa guida.

**La finestra si chiude subito.** Ogni voce del menu termina con una pausa; se la finestra sparisce
prima, lanciarla da un prompt dei comandi per leggere il messaggio:
`cmd /k "C:\percorso\della\libreria\avvia.bat"`.

**"Modifiche non salvate: SI" all'avvio.** Ci sono file modificati o nuovi non ancora registrati in
git: la voce `5` li salva (o, da terminale, `git status` li mostra).

**La voce `4` fallisce con rami "divergenti".** Sia il PC sia GitHub hanno commit che l'altro non
ha; `--ff-only` si ferma per non fare pasticci. Da terminale, nella cartella della libreria:
`git pull --rebase` (o `git pull --no-rebase` per un merge), risolvere gli eventuali conflitti, poi
voce `5`.

**"Copia codice" non fa nulla.** Alcuni browser non concedono l'accesso agli appunti alle pagine
aperte da `file://`; la pagina ricade sulla copia classica, ma se neanche quella funziona usare
**Mostra codice**, selezionare il testo e Ctrl+C, oppure **Apri .pl** e copiare dall'editor di testo.

**Percorsi.** Gli spazi nel percorso della libreria vanno bene (gli script li gestiscono). I
caratteri non ASCII (accenti) nel percorso di norma funzionano, ma in caso di problemi con `cmd.exe`
conviene un percorso semplice come `C:\Libreria-PowerLanguage`.

## Disinstallare

1. Se ci sono modifiche da conservare, prima la voce `5 Salva su GitHub (commit + push)`.
2. Cancellare la cartella della libreria (quella mostrata nella prima riga del menu).
3. Cancellare dal desktop il collegamento `Libreria PowerLanguage.lnk`.

Nient'altro viene scritto sul PC: niente registro di sistema, niente servizi. Restano solo, se
sono stati impostati dalla voce `5`, nome ed e-mail globali di git
(`git config --global --unset user.name` e `git config --global --unset user.email` per toglierli)
e, in *Gestione credenziali*, la voce `git:https://github.com` di Git Credential Manager
(eliminabile a mano). Git e Python restano installati (`winget uninstall --id Git.Git` e
`winget uninstall --id Python.Python.3.12` se non servono più).
