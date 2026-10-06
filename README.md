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
  `tools/build_catalog.py`: non va modificato a mano.
- `templates/` — modelli con placeholder usati da `tools/new_entry.py`.
- `docs/` — convenzioni, flusso di lavoro, istruzioni per il PowerLanguage Editor.

Ogni cartella di codice contiene almeno `README.md` (scheda con metadati YAML) e il sorgente `.pl` in
testo semplice, da incollare nel PowerLanguage Editor; opzionalmente l'archivio `.pla` esportato,
`notes.md` (note estese) e la sottocartella `backtests/` con immagini, export dello Strategy
Performance Report ed elenchi operazioni dei test. Ogni cartella fonte contiene `README.md` e,
opzionalmente, il PDF (`pdf:`) e `notes.md`.

## Struttura del repository

```
P/
├── README.md                     # questa panoramica
├── CATALOG.md                    # GENERATO da tools/build_catalog.py — non editare a mano
├── catalog.json                  # GENERATO — stesso contenuto in JSON
├── .gitignore
├── .gitattributes                # .pl/.cs/.md/.py/.csv/.html come testo; .pla/.pdf/.png/.jpg/.xlsx come binari
├── .editorconfig
├── docs/
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
│   └── tests/
│       ├── __init__.py
│       └── test_tools.py         # unittest (stdlib) per entrambi gli script
└── .github/workflows/validate.yml  # CI (Linux e Windows): test + build_catalog --check
```

## Avvio rapido

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
  si incolla il codice.

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
| `tools/tests/test_tools.py` | Test `unittest` (stdlib) per entrambi gli script. |

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

### Test e CI

```bash
python -m unittest discover -s tools/tests -v
python tools/build_catalog.py --check
```

Gli stessi due comandi sono eseguiti dalla CI (`.github/workflows/validate.yml`) a ogni push e pull
request, su Linux e su Windows.
