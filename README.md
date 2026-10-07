# Libreria PowerLanguage per MultiCharts

Archivio curato, con catalogo generato automaticamente, del codice **PowerLanguage** (indicatori,
strategie, funzioni) scritto per **MultiCharts** e dei **paper, libri e articoli** da cui quel codice
viene estratto. Ogni voce di codice dichiara da quale fonte deriva e da quali funzioni dipende; ogni
fonte ha una scheda con sintesi, formule, parametri e note di estrazione. Uno script verifica che i
collegamenti siano coerenti e produce il catalogo.

## Cosa contiene

- `indicators/` — indicatori (studi che disegnano plot sul grafico), uno per cartella.
- `strategies/` — strategie (in MultiCharts: *signal*), una per cartella.
- `functions/` — funzioni riutilizzabili richiamate da indicatori e strategie.
- `papers/` — schede delle fonti (paper, libri, capitoli, articoli, tesi, pagine web), una per cartella,
  con note di estrazione; il PDF locale è opzionale.
- `CATALOG.md` e `catalog.json` — il catalogo di tutto quanto sopra, **generato** da
  `tools/build_catalog.py`: non va modificato a mano. `catalog.html` è lo stesso catalogo come
  **pagina web locale** (ricerca, filtri per tag, pulsante "Copia codice"), generato da
  `tools/render_html.py` e ignorato da git.
- `templates/` — modelli con placeholder usati da `tools/new_entry.py`.
- `avvia.bat` e `tools/windows/` — avvio "a un clic" su Windows: menu in italiano, installazione
  su un PC nuovo, icona sul desktop (vedi [docs/WINDOWS.md](docs/WINDOWS.md)).
- `docs/` — guida Windows, convenzioni, flusso di lavoro, istruzioni per il PowerLanguage Editor.

Ogni cartella di codice contiene almeno `README.md` (scheda con metadati YAML) e il sorgente `.pl` in
testo semplice, da incollare nel PowerLanguage Editor; opzionalmente l'archivio `.pla` esportato,
`notes.md` (note estese) e la sottocartella `backtests/` con immagini, export dello Strategy
Performance Report ed elenchi operazioni dei test. Ogni cartella fonte contiene `README.md` e,
opzionalmente, il PDF (`pdf:`) e `notes.md`.

## Struttura del repository

```
P/
├── README.md                     # questa panoramica
├── avvia.bat                     # LAUNCHER Windows (doppio clic / icona sul desktop): menu in italiano
├── CATALOG.md                    # GENERATO da tools/build_catalog.py — non editare a mano
├── catalog.json                  # GENERATO — stesso contenuto in JSON
├── catalog.html                  # generato localmente da tools/render_html.py — ignorato da git
├── .gitignore                    # ignora anche catalog.html e i collegamenti *.lnk
├── .gitattributes                # testo LF: .pl/.cs/.md/.py/.csv/.html; testo CRLF: .bat/.cmd/.ps1; binari: .pla/.pdf/.png/.jpg/.xlsx/.ico
├── .editorconfig
├── docs/
│   ├── WINDOWS.md                # avvio a un clic su Windows: installa.bat, menu di avvia.bat, icona, problemi frequenti
│   ├── CONVENZIONI.md            # naming, schema metadati completo, stati, versioning, stile codice
│   ├── WORKFLOW.md               # dal paper al codice: estrazione → funzione → indicatore → strategia → test
│   └── MULTICHARTS.md            # come importare/esportare in PowerLanguage Editor, dipendenze, .pla vs .pl
├── templates/
│   ├── indicator/
│   │   ├── README.md             # front matter YAML + sezioni standard, con placeholder {{...}}
│   │   └── Indicator.pl          # scheletro indicatore
│   ├── strategy/
│   │   ├── README.md
│   │   └── Strategy.pl
│   ├── function/
│   │   ├── README.md
│   │   └── Function.pl
│   └── paper/
│       └── README.md             # scheda fonte (paper/libro/articolo) + sezione note di estrazione
├── indicators/<slug>/            # una cartella per indicatore: README.md + <Nome>.pl [+ .pla, notes.md]
│   └── backtests/                # (opzionale) immagini, report ed elenchi operazioni dei test
├── strategies/<slug>/            # una cartella per strategia
├── functions/<slug>/             # una cartella per funzione
├── papers/<paper-id>/            # una cartella per fonte: README.md [+ paper.pdf, notes.md]
├── tools/
│   ├── build_catalog.py          # valida metadati + genera CATALOG.md e catalog.json
│   ├── new_entry.py              # crea una nuova voce dai template
│   ├── render_html.py            # genera catalog.html: catalogo come pagina web locale con "Copia codice"
│   ├── wizard.py                 # procedura guidata in italiano che prepara ed esegue new_entry.py
│   ├── windows/
│   │   ├── installa.bat          # installazione su un PC nuovo: controlla git/python, clona, crea l'icona, apre il menu
│   │   ├── crea_collegamento.ps1 # crea "Libreria PowerLanguage.lnk" sul desktop (punta ad avvia.bat)
│   │   ├── libreria.ico          # icona del collegamento (binario, generato da make_icon.py)
│   │   └── make_icon.py          # genera libreria.ico in modo riproducibile (solo stdlib)
│   └── tests/
│       ├── __init__.py
│       ├── test_tools.py         # unittest (stdlib) per build_catalog.py e new_entry.py
│       ├── test_render_html.py   # unittest per render_html.py (e per l'ICO prodotto da make_icon.py)
│       └── test_wizard.py        # unittest per wizard.py
└── .github/workflows/validate.yml  # CI (Linux e Windows): test + build_catalog --check
```

## Avvio rapido su Windows: icona sul desktop

Su Windows non serve il terminale: un'icona sul desktop apre un menu in italiano che fa tutto
(catalogo come pagina web con il pulsante "Copia codice", procedura guidata per le nuove voci,
aggiornamento e salvataggio su GitHub, verifica). Requisiti: Windows 10/11, Git for Windows e
Python 3.10 o successivo; se mancano, la procedura propone di installarli con `winget`. La guida
completa, con i problemi frequenti, è [docs/WINDOWS.md](docs/WINDOWS.md).

1. **Scaricare `installa.bat`** (un solo file) da
   <https://raw.githubusercontent.com/tommaso0x/P/claude/powerlanguage-library-indicators-brr3a5/tools/windows/installa.bat>
   (nel browser: tasto destro → *Salva con nome*, lasciando il nome `installa.bat`). La parte
   `claude/powerlanguage-library-indicators-brr3a5` dell'indirizzo è il **nome del ramo**: se il
   ramo viene rinominato o unito in `main`, va sostituita con il nome nuovo. In alternativa, chi ha
   già clonato il repository (`git clone https://github.com/tommaso0x/P.git`) fa semplicemente
   doppio clic su `avvia.bat` nella cartella clonata.
2. **Doppio clic su `installa.bat`.** Controlla che Git e Python siano presenti (se mancano propone
   `winget install -e --id Python.Python.3.12` e `winget install -e --id Git.Git`), chiede la
   cartella di destinazione (Invio = `%USERPROFILE%\Documents\Libreria-PowerLanguage`), scarica la
   libreria con `git clone https://github.com/tommaso0x/P.git` (se la cartella contiene già la
   libreria la aggiorna con `git pull --ff-only`), crea l'icona e apre il menu. Se il repository è
   privato, al primo download Git Credential Manager chiede di accedere a GitHub.
3. **L'icona "Libreria PowerLanguage" compare sul desktop.** Un doppio clic apre il menu di
   `avvia.bat`. L'icona si può ricreare in qualunque momento con la voce `7` del menu o con
   `avvia.bat icona`.
4. **Cosa fa il menu** (`avvia.bat`; all'avvio mostra cartella, ramo, modifiche non salvate,
   versione di Python e se Git è disponibile):

   | Voce | Cosa fa |
   |---|---|
   | `1` Apri il catalogo (pagina web locale) | rigenera `catalog.html` con `tools\render_html.py --open` e lo apre nel browser: ricerca, filtri per tag, pulsante **Copia codice** per ogni voce |
   | `2` Apri la cartella della libreria | apre la cartella in Esplora file |
   | `3` Nuova voce (procedura guidata) | `tools\wizard.py`: domande in italiano, poi crea la voce chiamando `new_entry.py` |
   | `4` Aggiorna da GitHub (git pull) | `git pull --ff-only` |
   | `5` Salva su GitHub (commit + push) | rigenera il catalogo, `git add -A`, chiede il messaggio di commit (Invio = `Aggiornamento libreria <data>`), chiede nome ed e-mail per git se mancano, `git commit`, `git push` (`git push -u origin HEAD` al primo invio) |
   | `6` Verifica (test + catalogo) | `python -m unittest discover -s tools\tests` e `python tools\build_catalog.py --check` |
   | `7` Crea/aggiorna l'icona sul desktop | `tools\windows\crea_collegamento.ps1` |
   | `8` Apri la pagina GitHub del repository | apre <https://github.com/tommaso0x/P> nel browser |
   | `0` Esci | |

   Senza passare dal menu: `avvia.bat catalogo` rigenera e apre il catalogo, `avvia.bat icona` crea
   o aggiorna solo l'icona.

## Avvio rapido da terminale

Requisiti: Python ≥ 3.10, nessuna dipendenza esterna. Tutti i comandi si lanciano dalla radice del
repository.

1. **Aggiungere una fonte** (crea `papers/<id>/README.md` dal template):

   ```bash
   python tools/new_entry.py paper "Simple Technical Trading Rules and the Stochastic Properties of Stock Returns" \
     --authors "William Brock, Josef Lakonishok, Blake LeBaron" --year 1992 \
     --doi 10.1111/j.1540-6261.1992.tb04681.x
   ```

   L'id `1992-brock-lakonishok-lebaron-simple-technical-trading-rules` è derivato automaticamente
   (`--id` per forzarne uno diverso). Compilare la scheda: sintesi, regole/formule, parametri, note
   di estrazione.

2. **Aggiungere un indicatore o una strategia collegati alla fonte** (e, se serve, prima una funzione):

   ```bash
   python tools/new_entry.py function  "BLL_MA_Band_Signal" --slug bll-ma-band-signal \
     --paper 1992-brock-lakonishok-lebaron-simple-technical-trading-rules
   python tools/new_entry.py indicator "BLL1992 MA Band" --slug bll1992-ma-band \
     --paper 1992-brock-lakonishok-lebaron-simple-technical-trading-rules \
     --depends bll-ma-band-signal --tags moving-average,trend-following
   ```

   Scrivere il codice nel file `.pl` creato e compilare la scheda `README.md`.

3. **Incollare il codice nel PowerLanguage Editor** (File > New > Indicator/Signal/Function, incollare
   il testo del `.pl`, compilare). Importare prima le funzioni, poi gli studi che le usano. Dettagli in
   [docs/MULTICHARTS.md](docs/MULTICHARTS.md).

4. **Rigenerare il catalogo** e verificare che tutto sia coerente:

   ```bash
   python tools/build_catalog.py
   python tools/build_catalog.py --check
   ```

5. **Commit** di scheda, sorgente e catalogo rigenerato (`CATALOG.md`, `catalog.json`).

Il percorso completo, dalla lettura del paper al codice testato, è descritto in
[docs/WORKFLOW.md](docs/WORKFLOW.md).

## Convenzioni in breve

Il riferimento completo è [docs/CONVENZIONI.md](docs/CONVENZIONI.md).

- **Slug e id.** Le cartelle di codice usano slug in kebab-case minuscolo (`[a-z0-9]+(-[a-z0-9]+)*`,
  es. `bll1992-ma-band`); le fonti usano id `<anno>-<cognome-primo-autore>[-<altri-cognomi>]-<titolo-breve>`
  (es. `1992-brock-lakonishok-lebaron-simple-technical-trading-rules`). Lo slug/id nel front matter
  deve coincidere con il nome della cartella.
- **File sorgente.** Il nome del file `.pl` è il nome dello studio in MultiCharts con `_` al posto
  degli spazi (es. `BLL1992_MA_Band.pl`; se inizia con una cifra `new_entry.py` antepone `_`); per
  le funzioni il nome del file **deve** coincidere con il nome della funzione (errore del validatore
  in caso contrario).
- **Stati.** Codice: `draft → tested → stable → deprecated` (`tested` e `stable` dovrebbero indicare `multicharts_version`, altrimenti il validatore avvisa;
  `deprecated` indica il sostituto in `superseded_by`, altrimenti avvisa). Fonti:
  `to-read → reading → read → extracted`.
- **Versioning.** Semver `MAJOR.MINOR.PATCH` (solo tre numeri); ogni cambio di versione va annotato
  nel `## Changelog` della scheda, nella riga `Versione:` del `.pl` e aggiorna il campo `updated`.
- **`.pl` vs `.pla`.** In git si versiona sempre il sorgente in testo semplice `.pl` (diff, revisione,
  ricerca). L'archivio binario `.pla` esportato dall'editor è facoltativo e solo di comodo.
- **PDF e copyright.** Il PDF della fonte è opzionale: se non può essere ridistribuito, non va
  caricato e si lasciano solo `doi`/`url`; attenzione a filigrane e metadati personali e al fatto
  che un file committato resta nella storia di git. Per file grandi è possibile attivare Git LFS
  (riga commentata in `.gitattributes`).
- **Git.** Un ramo per catena logica (`paper/<paper-id>` o `study/<slug>`), merge su `main` con CI
  verde, messaggi in italiano con prefisso (`fonte:`, `funzione:`, `indicatore:`, `strategia:`,
  `docs:`, `tools:`), catalogo rigenerato in ogni commit: [docs/CONVENZIONI.md §12](docs/CONVENZIONI.md#12-git).
- **Windows.** I file di testo sono normalizzati a LF nel repository (`.gitattributes`); nel working
  copy possono essere CRLF con `core.autocrlf=true`; il PowerLanguage Editor accetta entrambi quando
  si incolla il codice. Fanno eccezione gli script `.bat`, `.cmd` e `.ps1`, che sono CRLF anche nel
  repository (`eol=crlf`) e contengono solo caratteri ASCII. L'uso "a un clic" (icona, menu) è
  descritto in [docs/WINDOWS.md](docs/WINDOWS.md).

## Catalogo

[CATALOG.md](CATALOG.md) elenca tutte le voci (una tabella per tipo, con versione, stato e
versione di MultiCharts testata), le fonti, la mappa fonte → implementazioni, l'**indice per tag**
(tag → voci di codice) e le voci senza fonte; [catalog.json](catalog.json) contiene gli stessi dati
in JSON, comodi da interrogare da riga di comando, per esempio per elencare le voci con un tag:

```bash
python -c "import json;[print(e['path']) for e in json.load(open('catalog.json'))['entries'] if 'moving-average' in e['tags']]"
```

Entrambi sono **generati** da `python tools/build_catalog.py` e non vanno modificati a mano:
ogni modifica va fatta nelle schede e poi si rigenera il catalogo. La CI esegue
`build_catalog.py --check` e fallisce se i metadati non sono validi o il catalogo non è aggiornato.

Lo stesso catalogo si consulta anche come **pagina web locale**: `python tools/render_html.py --open`
genera `catalog.html` nella radice (una sola pagina, senza risorse esterne, funziona da `file://`)
e lo apre nel browser, con ricerca, filtri per tag e, per ogni voce di codice, i pulsanti
**Copia codice**, **Mostra codice**, **Scheda**, **Apri cartella** e **Apri .pl**. `catalog.html` è
generato localmente e ignorato da git (non fa parte di `--check`): su Windows lo apre la voce `1`
del menu di `avvia.bat`.

## Esempio incluso

La libreria include una catena completa tratta da Brock, Lakonishok e LeBaron (1992), *Simple
Technical Trading Rules and the Stochastic Properties of Stock Returns*, The Journal of Finance,
47(5), 1731–1764:

| Passo | Voce | Cartella |
|---|---|---|
| Fonte | scheda del paper, con regole VMA / FMA / TRB e note di estrazione | [papers/1992-brock-lakonishok-lebaron-simple-technical-trading-rules/](papers/1992-brock-lakonishok-lebaron-simple-technical-trading-rules/README.md) |
| Funzione | `BLL_MA_Band_Signal`: +1 / −1 / 0 rispetto alla banda intorno alla media lunga | [functions/bll-ma-band-signal/](functions/bll-ma-band-signal/README.md) |
| Indicatore | `BLL1992 MA Band`: media breve, media lunga, banda superiore e inferiore | [indicators/bll1992-ma-band/](indicators/bll1992-ma-band/README.md) |
| Strategia | `BLL1992 MA Crossover`: incrocio di medie con banda; `HoldDays = 0` → VMA, `> 0` → FMA | [strategies/bll1992-ma-crossover/](strategies/bll1992-ma-crossover/README.md) |
| Strategia | `BLL1992 Trading Range Breakout`: rottura del massimo/minimo degli ultimi `Length` giorni | [strategies/bll1992-trading-range-breakout/](strategies/bll1992-trading-range-breakout/README.md) |

L'indicatore e le due strategie dichiarano `papers: [1992-brock-...]`; indicatore e strategia di
incrocio dichiarano `depends_on: [bll-ma-band-signal]`, quindi in MultiCharts la funzione va
importata per prima.

## Licenza

Repository privato: nessuna licenza dichiarata, tutti i diritti riservati al proprietario. Prima di
pubblicarlo: scegliere una licenza (es. MIT) e aggiungere un file `LICENSE`; verificare che nessun
PDF o testo protetto da copyright sia nel repository **o nella sua storia** (vedi
[docs/CONVENZIONI.md §10](docs/CONVENZIONI.md#10-pdf-copyright-e-file-grandi)).

## Strumenti

| Script | Scopo |
|---|---|
| `tools/build_catalog.py` | Valida i metadati di tutte le voci e genera `CATALOG.md` e `catalog.json`. |
| `tools/new_entry.py` | Crea una nuova voce (indicatore, strategia, funzione o fonte) copiando il template e sostituendo i placeholder. |
| `tools/render_html.py` | Genera `catalog.html`, il catalogo come pagina web locale (ricerca, tag, "Copia codice", schede e sorgenti in pagina); ignorato da git. |
| `tools/wizard.py` | Procedura guidata in italiano: fa le domande, mostra il comando `new_entry.py` equivalente e lo esegue dopo conferma. |
| `tools/windows/` | Avvio a un clic su Windows: `installa.bat` (installazione su un PC nuovo), `crea_collegamento.ps1` (icona sul desktop), `libreria.ico` e `make_icon.py` (l'icona e il suo generatore). Il menu è `avvia.bat` nella radice. |
| `tools/tests/` | Test `unittest` (stdlib): `test_tools.py` (build_catalog, new_entry), `test_render_html.py` (render_html, make_icon), `test_wizard.py` (wizard). |

Requisiti: Python ≥ 3.10, solo libreria standard (nessuna dipendenza da installare: il front matter è letto da un parser integrato, PyYAML non è
usato).

### `tools/build_catalog.py`

```bash
python tools/build_catalog.py            # valida + scrive CATALOG.md e catalog.json; exit 0
python tools/build_catalog.py --check    # valida + verifica che CATALOG.md/catalog.json siano aggiornati;
                                         # exit 1 con messaggi chiari se i metadati non sono validi o il catalogo è obsoleto
python tools/build_catalog.py --root <path>   # radice del repository (default: cartella padre di tools/)
python tools/build_catalog.py --quiet         # non stampa avvisi e messaggi informativi
```

Comportamento:

- Scansiona `indicators/`, `strategies/`, `functions/`, `papers/` cercando `*/README.md`
  (`templates/` è ignorata) e legge il front matter YAML con un parser integrato che accetta il
  sottoinsieme semplice descritto in `docs/CONVENZIONI.md` (scalari, liste flow `[a, b]` o a blocchi).
- Valida: campi obbligatori presenti; `type` coerente con la cartella; `slug`/`id` uguale al nome
  della cartella e conforme alla regex; `source_file` esistente; `archive_file`/`pdf` esistenti se
  indicati; ogni id in `papers:` esistente in `papers/`; ogni slug in `depends_on:` esistente in
  `functions/` (e diverso dalla voce stessa); per le funzioni `source_file` senza `.pl` uguale a
  `name`; `status` tra i valori ammessi; `version` esattamente `MAJOR.MINOR.PATCH`; date ISO
  `YYYY-MM-DD`; nessun slug/id duplicato; `superseded_by`, se presente, slug di una voce esistente e
  diversa dalla voce stessa. Raccoglie **tutti** gli errori, li stampa come
  `ERRORE <percorso>: <messaggio>` ed esce con codice 1.
- Avvisi non bloccanti (`AVVISO <percorso>: <messaggio>`): fonte senza implementazioni; voce di
  codice con `papers: []`; `tested`/`stable` senza `multicharts_version`; versione diversa tra front
  matter, riga `Versione:` dell'intestazione del `.pl` e prima riga del `## Changelog`; chiave
  sconosciuta nel front matter; fonte la cui sezione `## Implementazioni in questa libreria` non
  elenca una voce che la cita (il catalogo è la mappa autorevole; l'avviso dice quale scheda
  aggiornare); `deprecated` senza `superseded_by`.
- Genera `CATALOG.md` con: intestazione che dichiara il file generato e il comando per rigenerarlo;
  conteggi; una tabella per tipo (Nome | Slug | Versione | Stato | MC | Fonti | Dipendenze | Tag)
  con link relativi a ogni `README.md`, dove `MC` è `multicharts_version`, il nome ha il suffisso
  del linguaggio quando non è PowerLanguage (es. `(PowerLanguage.NET)`) e lo stato diventa
  `deprecated → [slug]` se `superseded_by` è impostato; la tabella "Fonti" (Anno | Titolo | Autori |
  Tipo | Stato | Implementazioni); la sezione "Mappa fonte → implementazioni"; la sezione "Indice
  per tag" (tag → voci di codice); la sezione "Voci senza fonte". L'output è deterministico
  (ordinato, senza timestamp), così `--check` è stabile.
- Genera `catalog.json`: `{"generated_by": "tools/build_catalog.py", "entries": [...], "papers": [...]}`
  con tutti i campi letti più `"path"`.

### `tools/new_entry.py`

```bash
python tools/new_entry.py indicator "BLL1992 MA Band" [--slug bll1992-ma-band] [--paper <id> ...] \
       [--depends <function-slug> ...] [--tags a,b] [--summary "..."]
python tools/new_entry.py strategy "..." ...
python tools/new_entry.py function "..." ...
python tools/new_entry.py paper "Simple Technical Trading Rules..." --authors "William Brock, Josef Lakonishok" \
       --year 1992 [--id <id>] [--type paper|book|chapter|article|thesis|web] [--doi ...] [--url ...] [--tags ...]
```

Opzioni comuni: `--root <path>` (radice del repository), `--date YYYY-MM-DD` (default: oggi),
`--force` (se la cartella esiste già, riscrive i file generati dal template salvando prima una copia
di ogni file sovrascritto in `<file>.bak`, ignorato da git; gli altri file restano),
`--dry-run` (mostra cosa verrebbe creato senza scrivere). `--paper`, `--depends` e `--tags` si
possono ripetere o ricevere più valori separati da virgola.

Comportamento:

- Se `--slug` manca, lo slug è derivato dal nome (caratteri ridotti ad ASCII, kebab-case). Se `--id`
  manca, l'id della fonte è derivato come `<anno>-<cognomi di al più 3 autori>-<prime 5 parole del titolo in slug>`,
  senza le parole vuote (*the*, *and*, *of*, ...): per l'esempio BLL si ottiene
  `1992-brock-lakonishok-lebaron-simple-technical-trading-rules`.
- Copia `templates/<tipo>/` nella cartella di destinazione sostituendo i placeholder `{{...}}`:
  `{{NAME}}`, `{{SLUG}}`, `{{SOURCE_FILE}}`, `{{SOURCE_NAME}}` (nome del file senza `.pl`, usato
  come identificatore della funzione), `{{PAPERS}}`, `{{DEPENDS_ON}}`, `{{TAGS}}`, `{{DATE}}`,
  `{{SUMMARY}}`, `{{TYPE}}` e, per le fonti, `{{ID}}`, `{{TITLE}}`, `{{AUTHORS}}`, `{{YEAR}}`,
  `{{DOI}}`, `{{URL}}`, `{{PAPER_TYPE}}`, `{{CITATION}}`. Nel front matter i valori che lo
  richiedono (per esempio con `: ` o ` #`) sono messi tra virgolette automaticamente.
- Rinomina il template del sorgente in `<NomeFile>.pl`, dove il nome è quello dello studio con gli
  spazi sostituiti da `_` e i caratteri non alfanumerici rimossi (es. `"BLL1992 MA Band"` →
  `BLL1992_MA_Band.pl`); se il risultato inizia con una cifra viene anteposto `_` (es. `"200 Day MA"`
  → `_200_Day_MA.pl`), perché un identificatore PowerLanguage non può iniziare con una cifra.
- Rifiuta di sovrascrivere una cartella esistente senza `--force`. Se una fonte in `--paper` o una
  funzione in `--depends` non esiste ancora, stampa un avviso ma crea comunque la voce (sarà
  `build_catalog.py` a segnalare l'errore finché il riferimento non esiste). Al termine stampa i
  percorsi creati e i passi successivi: compilare la scheda, incollare il codice, eseguire
  `build_catalog.py`.

### `tools/render_html.py`

```bash
python tools/render_html.py                 # valida, rigenera CATALOG.md/catalog.json se non aggiornati, scrive catalog.html
python tools/render_html.py --open          # ...e apre la pagina nel browser predefinito
python tools/render_html.py --out X.html    # percorso di uscita diverso (i link relativi vengono adattati)
python tools/render_html.py --root <path>   # radice del repository (default: cartella padre di tools/)
python tools/render_html.py --quiet         # non stampa avvisi e messaggi informativi
python tools/render_html.py --stamp         # aggiunge la riga "Generato il ..." (senza, l'output è deterministico)
python tools/render_html.py --no-catalog    # non rigenera CATALOG.md e catalog.json anche se non aggiornati
```

Comportamento:

- Non rilegge i metadati per conto suo: importa `tools/build_catalog.py` e ne usa caricatore,
  validatore e renderer. Se ci sono errori di validazione li stampa (`ERRORE ...`) ed esce con
  codice 1 senza scrivere nulla.
- Legge, oltre a `catalog.json`, il corpo di ogni scheda `README.md` (dopo il front matter) e il
  sorgente di ogni voce di codice, e produce **una sola pagina** `catalog.html` autosufficiente (CSS
  e JavaScript inline, nessuna risorsa esterna, funziona da `file://`), in italiano, chiara/scura
  secondo il sistema, leggibile anche da telefono.
- Struttura: intestazione con titolo, conteggi, casella di ricerca (filtra le schede per testo) e
  tag cliccabili (filtrano); sezioni **Indicatori**, **Strategie**, **Funzioni**, **Fonti**. Ogni
  scheda di codice mostra nome, tipo, stato, versione, linguaggio se diverso da PowerLanguage,
  sintesi, tag, **Fonti** e **Dipendenze** (link interni alla pagina) e i pulsanti **Copia codice**
  (copia tutto il `.pl` negli appunti e conferma con "Copiato!"), **Mostra codice**, **Scheda** (la
  `README.md` resa in HTML), **Apri cartella**, **Apri .pl**. Ogni scheda di fonte mostra titolo,
  autori, anno, tipo, stato, rivista/volume/numero/pagine se presenti, link DOI/URL (in una nuova
  scheda del browser), tag, **Implementazioni** (link interni), **Scheda**, e i link a `notes.md`
  e al PDF se presenti.
- Il Markdown delle schede è reso da un renderer minimo integrato (intestazioni, paragrafi, elenchi,
  tabelle, blocchi di codice, citazioni, codice in linea, grassetto, corsivo, link); tutto il resto
  è protetto con escape HTML e il renderer non si interrompe su input strani. L'output è
  deterministico (nessun timestamp senza `--stamp`).
- `catalog.html` è un file **locale**: `.gitignore` lo esclude e `build_catalog.py --check` non lo
  considera. Si rigenera quando serve.

### `tools/wizard.py`

```bash
python tools/wizard.py                      # procedura guidata interattiva, in italiano
python tools/wizard.py --root <path>        # radice del repository (default: cartella padre di tools/)
python tools/wizard.py --dry-run            # mostra cosa verrebbe creato senza scrivere (passato a new_entry.py)
python tools/wizard.py --date AAAA-MM-GG    # data da scrivere nei metadati (default: oggi)
```

Fa una domanda alla volta: tipo di voce (`1` indicatore, `2` strategia, `3` funzione, `4` fonte);
nome (o titolo); per le voci di codice le fonti scelte da un elenco numerato delle fonti esistenti
(più numeri separati da virgola, Invio per nessuna, oppure un nuovo id), le dipendenze dall'elenco
numerato delle funzioni esistenti, i tag (separati da virgola, con i tag già in uso come
suggerimento) e la sintesi in una riga; per le fonti autori, anno, tipo
(`paper`/`book`/`chapter`/`article`/`thesis`/`web`), DOI, URL, tag e sintesi. Per le funzioni
avverte che il nome deve essere un identificatore PowerLanguage valido (lettere, cifre e `_`, non
può iniziare con una cifra) e rifiuta gli altri; un nome vuoto viene richiesto. Propone lo slug (o
l'id) derivato, modificabile con Invio per accettarlo, poi mostra il comando `new_entry.py` esatto,
chiede conferma e chiama `new_entry.main([...])` nello stesso processo. Al termine elenca i file creati e i passi successivi (compilare la scheda,
incollare il codice nel `.pl`, eseguire la voce `6 Verifica` del menu) e, su Windows, propone di
aprire la cartella. Ctrl+C esce in modo pulito con un messaggio. Su Windows è la voce `3` del menu
di `avvia.bat`.

### `avvia.bat` e `tools/windows/`

```bat
avvia.bat                 :: menu (voci 1-8, 0 per uscire)
avvia.bat catalogo        :: rigenera e apre il catalogo, poi esce
avvia.bat icona           :: crea/aggiorna solo l'icona sul desktop, poi esce
tools\windows\installa.bat   :: installazione su un PC nuovo (da scaricare e avviare con doppio clic)
powershell -NoProfile -ExecutionPolicy Bypass -File tools\windows\crea_collegamento.ps1 -Repo "<cartella>"
python tools\windows\make_icon.py   :: rigenera libreria.ico (riproducibile)
```

`crea_collegamento.ps1` crea sul desktop (anche se spostato su OneDrive) il collegamento
`Libreria PowerLanguage.lnk`, che avvia `avvia.bat` nella cartella della libreria con l'icona
`tools/windows/libreria.ico`; senza `-Repo` usa la cartella padre di `tools/windows/`. Gli script
`.bat`/`.ps1` sono in ASCII e con fine riga CRLF. Tutto il resto, compresi i problemi frequenti, è
in [docs/WINDOWS.md](docs/WINDOWS.md).

### Test e CI

```bash
python -m unittest discover -s tools/tests -v
python tools/build_catalog.py --check
```

Gli stessi due comandi sono eseguiti dalla CI (`.github/workflows/validate.yml`) a ogni push e pull
request, su Linux e su Windows; su Windows li lancia anche la voce `6 Verifica (test + catalogo)` del
menu di `avvia.bat`. `python -m unittest discover` trova tutti i file `tools/tests/test_*.py`.
