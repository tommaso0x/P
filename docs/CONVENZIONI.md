# Convenzioni

Riferimento completo per nomi, metadati, stati, versioni e stile del codice. Tutto ciò che è
descritto qui viene verificato, dove possibile, da `tools/build_catalog.py`: una scheda non conforme
produce un `ERRORE <percorso>: <messaggio>` e il catalogo non viene generato.

`CATALOG.md` e `catalog.json` sono **generati** da `python tools/build_catalog.py` e non vanno
modificati a mano.

## 1. Contenuto di una voce

**Voce di codice** (`indicators/<slug>/`, `strategies/<slug>/`, `functions/<slug>/`):

| File | Obbligatorio | Contenuto |
|---|---|---|
| `README.md` | sì | scheda: front matter YAML (§4) + sezioni standard (§6) |
| `<NomeFile>.pl` | sì | sorgente PowerLanguage in testo semplice, da incollare nel PowerLanguage Editor; indicato in `source_file` |
| `<Nome>.pla` | no | archivio PowerLanguage esportato dall'editor (binario); indicato in `archive_file` |
| `notes.md` | no | note estese (vedi sotto) |
| `backtests/` | no | risultati dei test: immagini (`*.png`, `*.jpg`), export dello Strategy Performance Report (`*.xlsx`, `*.html`), elenco operazioni (`*.csv`); nome file `<AAAA-MM-GG>_<strumento>_<timeframe>_<descrizione>.<ext>` (es. `2026-10-06_DJIA_daily_vma-1-50-001.png`); ogni file va citato in `## Test e risultati` |

**Fonte** (`papers/<paper-id>/`):

| File | Obbligatorio | Contenuto |
|---|---|---|
| `README.md` | sì | scheda: front matter YAML (§5) + sezioni standard (§6) |
| `paper.pdf` (o altro nome) | no | PDF locale, indicato nel campo `pdf`; vedi §10 per il copyright |
| `notes.md` | no | note di estrazione estese (vedi sotto) |

**`notes.md`.** Quando `## Note di estrazione` (fonti) o `## Note di implementazione` (codice)
superano circa 30 righe, il dettaglio va spostato in `notes.md` nella stessa cartella; nel
`README.md` resta una sintesi seguita dal link `Note estese: [notes.md](notes.md)`. `notes.md` è
Markdown libero, senza front matter: il validatore non lo legge.

## 2. Nomi di cartelle e file

### Slug delle voci di codice

- Regex: `[a-z0-9]+(-[a-z0-9]+)*` — minuscolo, kebab-case, solo lettere ASCII, cifre e trattini
  singoli; niente trattini iniziali/finali, niente underscore, niente accenti.
- Lo slug è il nome della cartella **e** il valore del campo `slug` nel front matter: devono coincidere.
- Deve essere unico in tutta la libreria (tra `indicators/`, `strategies/` e `functions/`).
- `tools/new_entry.py` lo deriva dal nome dello studio (riduzione ad ASCII, kebab-case); si può
  forzare con `--slug`.
- Esempi: `bll-ma-band-signal`, `bll1992-ma-band`, `bll1992-trading-range-breakout`.

### Id delle fonti

- Formato: `<anno>-<cognome-primo-autore>[-<secondo-cognome>...]-<titolo-breve-slug>`, stessa
  regex degli slug.
- È il nome della cartella **e** il valore del campo `id`: devono coincidere. Deve essere unico.
- `tools/new_entry.py` lo deriva come `<anno>-<cognomi di al più 3 autori>-<prime 5 parole del titolo>`,
  togliendo dalle parole del titolo le parole vuote (articoli, congiunzioni, preposizioni come *the*,
  *and*, *of*); se il risultato non piace, passare `--id`.
- Esempio: da "Simple Technical Trading Rules and the Stochastic Properties of Stock Returns" (1992,
  Brock, Lakonishok, LeBaron) la derivazione automatica produce
  `1992-brock-lakonishok-lebaron-simple-technical-trading-rules`.

### File sorgente `.pl`

- Nome in PascalCase/underscore **uguale al nome dello studio in MultiCharts**, estensione `.pl`,
  contenuto in testo semplice (UTF-8, fine riga LF).
- Regola di derivazione usata da `new_entry.py`: spazi → `_`, caratteri non alfanumerici rimossi;
  se il risultato inizia con una cifra viene anteposto `_` (un identificatore PowerLanguage non può
  iniziare con una cifra). Esempi: `"BLL1992 MA Band"` → `BLL1992_MA_Band.pl`;
  `"200 Day MA"` → `_200_Day_MA.pl`.
- Per le **funzioni** il nome del file (senza estensione) **deve** essere identico al nome della
  funzione, perché MultiCharts richiede che il nome della funzione coincida con il nome dello studio
  e la funzione viene richiamata nel codice con quel nome. Esempio: funzione `BLL_MA_Band_Signal` →
  file `BLL_MA_Band_Signal.pl`. Se `name` e nome del file (senza `.pl`) non coincidono,
  `build_catalog.py` lo segnala come **errore** e il catalogo non viene generato.
- Un solo file sorgente per voce: se uno studio richiede più pezzi di codice, le parti comuni
  diventano funzioni separate in `functions/` dichiarate in `depends_on`.

## 3. Front matter YAML: sottoinsieme ammesso

Il front matter è il blocco tra due righe `---` all'inizio di `README.md`. Il parser di
`build_catalog.py` è interno (nessuna dipendenza) e accetta **solo** questo sottoinsieme di YAML:

- scalari su una riga: `chiave: valore` — stringhe (con o senza virgolette), numeri, booleani
  (`true`/`false`);
- liste piatte in stile flow `chiave: [a, b, c]` oppure a blocchi:

  ```yaml
  tags:
    - moving-average
    - trend-following
  ```

- righe di commento che iniziano con `#` (i template le usano per i campi opzionali) e commenti in
  linea `# ...` preceduti da uno spazio: vengono ignorati;
- un valore vuoto (`chiave:`, `null`, `~`) equivale a campo assente;
- **non** ammessi: mappature annidate, stringhe su più righe, ancore/alias.

Le chiavi ammesse sono quelle dei §4 e §5: una chiave sconosciuta (per esempio un refuso come
`tag:` invece di `tags:`) produce un avviso `AVVISO <percorso>: campo 'tag' non previsto dallo schema (refuso?); i campi
ammessi sono in docs/CONVENZIONI.md`.

Suggerimenti: mettere tra virgolette i valori che contengono `: ` (due punti e spazio) o ` #`
(spazio e cancelletto), altrimenti la parte dopo ` #` viene letta come commento; mettere tra
virgolette i numeri che devono restare stringhe (`multicharts_version: "14"`); scrivere le date
come `YYYY-MM-DD` senza virgolette. `new_entry.py` aggiunge le virgolette da solo dove servono.

## 4. Schema metadati — voci di codice

### Campi obbligatori

| Campo | Tipo | Valori ammessi | Esempio | Note |
|---|---|---|---|---|
| `type` | stringa | `indicator`, `strategy`, `function` | `indicator` | deve corrispondere alla cartella: `indicators/` → `indicator`, `strategies/` → `strategy`, `functions/` → `function` |
| `name` | stringa | testo libero | `BLL1992 MA Band` | nome dello studio esattamente come appare in MultiCharts |
| `slug` | stringa | regex §2 | `bll1992-ma-band` | uguale al nome della cartella; unico |
| `version` | stringa | `MAJOR.MINOR.PATCH` (§8) | `1.0.0` | |
| `status` | stringa | `draft`, `tested`, `stable`, `deprecated` | `draft` | ciclo di vita in §7 |
| `language` | stringa | `PowerLanguage`, `PowerLanguage.NET` | `PowerLanguage` | `.NET` ammesso ma fuori dall'ambito delle guide |
| `source_file` | stringa | nome di un file nella stessa cartella | `BLL1992_MA_Band.pl` | il file deve esistere |
| `papers` | lista | id esistenti in `papers/` | `[1992-brock-lakonishok-lebaron-simple-technical-trading-rules]` | può essere `[]` (produce un avviso: voce senza fonte) |
| `depends_on` | lista | slug esistenti in `functions/` | `[bll-ma-band-signal]` | funzioni richieste, da importare prima in MultiCharts; `[]` se nessuna; una voce non può elencare se stessa |
| `tags` | lista | parole in kebab-case | `[moving-average, trend-following]` | usate nel catalogo |
| `created` | data | `YYYY-MM-DD` | `2026-10-06` | data di creazione della voce |
| `updated` | data | `YYYY-MM-DD` | `2026-10-06` | data dell'ultima modifica; da aggiornare a ogni cambio di versione o stato |

### Campi opzionali

| Campo | Tipo | Valori ammessi | Esempio | Note |
|---|---|---|---|---|
| `archive_file` | stringa | nome di un file `.pla` nella stessa cartella | `BLL1992_MA_Band.pla` | se indicato, il file deve esistere |
| `multicharts_version` | stringa | testo | `"14"` | versione di MultiCharts su cui il codice è stato compilato/testato; tra virgolette; attesa per `tested` e `stable` (altrimenti avviso); mostrata nella colonna `MC` del catalogo |
| `markets` | lista | testo libero | `[indici azionari]` | mercati su cui è stato testato o pensato |
| `timeframes` | lista | testo libero | `[daily]` | timeframe di riferimento |
| `author` | stringa | testo | `tommaso0x` | chi ha scritto il codice |
| `summary` | stringa | una riga | `Una riga di descrizione.` | mostrata nel catalogo |
| `superseded_by` | stringa | slug di una voce di codice esistente | `bll1992-ma-band-v2` | richiesto per convenzione quando `status: deprecated` (avviso se manca); errore se lo slug non esiste o è la voce stessa; nel catalogo lo Stato diventa `deprecated → [slug]` |

### Esempio completo

```yaml
---
type: indicator
name: BLL1992 MA Band
slug: bll1992-ma-band
version: 1.0.0
status: draft
language: PowerLanguage
source_file: BLL1992_MA_Band.pl
papers: [1992-brock-lakonishok-lebaron-simple-technical-trading-rules]
depends_on: [bll-ma-band-signal]
tags: [moving-average, trend-following]
created: 2026-10-06
updated: 2026-10-06
archive_file: BLL1992_MA_Band.pla
multicharts_version: "14"
markets: [indici azionari]
timeframes: [daily]
author: tommaso0x
summary: Media breve, media lunga e banda ±b come in Brock, Lakonishok e LeBaron (1992).
---
```

## 5. Schema metadati — fonti

### Campi obbligatori

| Campo | Tipo | Valori ammessi | Esempio | Note |
|---|---|---|---|---|
| `type` | stringa | `paper`, `book`, `chapter`, `article`, `thesis`, `web` | `paper` | `paper` = articolo accademico; `article` = articolo divulgativo/rivista di settore; `web` = pagina web, post |
| `id` | stringa | regex §2 | `1992-brock-lakonishok-lebaron-simple-technical-trading-rules` | uguale al nome della cartella; unico |
| `title` | stringa | testo | `Simple Technical Trading Rules and the Stochastic Properties of Stock Returns` | titolo originale, non tradotto |
| `authors` | lista | `Nome Cognome` | `[William Brock, Josef Lakonishok, Blake LeBaron]` | nell'ordine della pubblicazione; almeno un autore |
| `year` | intero | anno | `1992` | anno di pubblicazione |
| `status` | stringa | `to-read`, `reading`, `read`, `extracted` | `extracted` | ciclo di vita in §7 |
| `tags` | lista | parole in kebab-case | `[technical-analysis, moving-average, trading-range-breakout]` | |
| `added` | data | `YYYY-MM-DD` | `2026-10-06` | data di inserimento nella libreria |

### Campi opzionali

| Campo | Tipo | Esempio | Note |
|---|---|---|---|
| `journal` | stringa | `The Journal of Finance` | rivista (per `paper`/`article`) |
| `volume` | intero o stringa | `47` | |
| `issue` | intero o stringa | `5` | |
| `pages` | stringa | `1731-1764` | intervallo di pagine |
| `publisher` | stringa | `Wiley` | editore (soprattutto per `book`/`chapter`) |
| `doi` | stringa | `10.1111/j.1540-6261.1992.tb04681.x` | solo il DOI, senza prefisso `https://doi.org/` |
| `url` | stringa | `https://doi.org/10.1111/j.1540-6261.1992.tb04681.x` | link alla fonte (DOI risolto, pagina dell'editore, SSRN, ...) |
| `pdf` | stringa | `paper.pdf` | file locale nella cartella; se indicato deve esistere; vedi §10 |
| `isbn` | stringa | `"978-..."` | per libri; tra virgolette |
| `summary` | stringa | `Una riga.` | mostrata nel catalogo |

### Esempio completo

```yaml
---
type: paper
id: 1992-brock-lakonishok-lebaron-simple-technical-trading-rules
title: Simple Technical Trading Rules and the Stochastic Properties of Stock Returns
authors: [William Brock, Josef Lakonishok, Blake LeBaron]
year: 1992
status: extracted
tags: [technical-analysis, moving-average, trading-range-breakout]
added: 2026-10-06
journal: The Journal of Finance
volume: 47
issue: 5
pages: 1731-1764
doi: 10.1111/j.1540-6261.1992.tb04681.x
url: https://doi.org/10.1111/j.1540-6261.1992.tb04681.x
summary: Test di regole di media mobile e trading range breakout sul Dow Jones 1897-1986.
---
```

## 6. Sezioni standard delle schede

Le intestazioni sono in italiano e in quest'ordine; i template in `templates/` le contengono già con
un suggerimento in commento HTML per ciascuna. Una sezione senza contenuto resta con la sola
intestazione (non va rimossa).

**Voce di codice** (`# <name>` come titolo, poi):

1. `## Descrizione` — cosa fa lo studio, in due o tre frasi.
2. `## Fonte` — elenco puntato con link a `../../papers/<id>/README.md` per ogni id in `papers`.
3. `## Logica` — regole e formule implementate, con la corrispondenza alla notazione del paper.
4. `## Input` — tabella `Nome | Tipo | Default | Descrizione`.
5. `## Output` — plot (indicatori), ordini generati (strategie) o valore di ritorno (funzioni).
6. `## Dipendenze` — funzioni richieste (quelle in `depends_on`) e funzioni built-in rilevanti.
7. `## Note di implementazione` — scelte fatte nel tradurre il paper in codice, limiti, differenze.
8. `## Test e risultati` — versione di MultiCharts, dati, periodo, risultati del backtest, con un
   riferimento a ogni file salvato in `backtests/` (§1).
9. `## Changelog` — una riga per versione, la più recente in alto, nel formato dei template:
   `- 2026-10-20 — 1.1.0: cosa è cambiato`.

**Fonte** (`# <title>` come titolo, poi):

1. `## Riferimento` — citazione completa in stile APA.
2. `## Sintesi` — di cosa tratta e cosa conclude.
3. `## Idee chiave` — elenco puntato.
4. `## Regole / Formule` — come sono scritte nel paper, con la notazione del paper.
5. `## Parametri usati nel paper` — valori e combinazioni testate dagli autori.
6. `## Dati e risultati del paper` — in breve: dataset, periodo, risultati principali.
7. `## Note di estrazione` — cosa era ambiguo e quali decisioni sono state prese nel passare al codice.
8. `## Implementazioni in questa libreria` — link a `../../<tipo>s/<slug>/README.md`; il catalogo
   ricava la stessa mappa dal campo `papers:` delle voci di codice ed è la mappa autorevole: se una
   voce cita la fonte ma non è elencata in questa sezione, `build_catalog.py` emette un avviso che
   indica quale scheda aggiornare.
9. `## Riferimenti correlati` — altri paper, libri o voci collegate.

## 7. Ciclo di vita degli stati

### Codice: `draft → tested → stable → deprecated`

| Stato | Significato | Condizione per entrarci |
|---|---|---|
| `draft` | bozza: codice in scrittura o non ancora verificato | stato iniziale di ogni nuova voce |
| `tested` | compila nel PowerLanguage Editor, è stato eseguito su un grafico/backtest e il comportamento è stato confrontato con le regole del paper | la sezione `## Test e risultati` è compilata (dati, periodo, esito) e il front matter ha `multicharts_version` (la versione su cui è stato eseguito il test; senza, il validatore avvisa) |
| `stable` | usato nel tempo senza correzioni di rilievo; l'interfaccia degli input è considerata definitiva | almeno una versione `tested` consolidata; ogni modifica successiva passa da un cambio di versione |
| `deprecated` | superato o non più mantenuto | il campo `superseded_by` indica lo slug della voce che lo sostituisce (avviso se manca) e la sezione `## Descrizione` spiega perché; nel catalogo compare `deprecated → [slug]` |

Si torna a `draft` se una modifica rende il comportamento non verificato (per esempio un cambio di
`MAJOR`). Ogni cambio di stato aggiorna `updated` e viene annotato nel `## Changelog`.

### Fonti: `to-read → reading → read → extracted`

| Stato | Significato |
|---|---|
| `to-read` | scheda creata (riferimento e link), fonte non ancora letta |
| `reading` | lettura in corso; `## Sintesi` e `## Idee chiave` parziali |
| `read` | lettura completata; `## Regole / Formule`, `## Parametri usati nel paper` e `## Note di estrazione` compilate |
| `extracted` | almeno una voce di codice in questa libreria la cita in `papers:` |

`build_catalog.py` segnala con un avviso ogni fonte che nessuna voce cita (fonte senza
implementazioni), qualunque sia il suo stato: è normale per `to-read`, `reading` e `read`, mentre
per una fonte `extracted` indica un'incoerenza: o si aggiunge l'implementazione o si riporta lo
stato a `read`.

## 8. Versioning (semver)

- Formato `MAJOR.MINOR.PATCH`, solo tre numeri interi separati da punto (es. `1.0.0`, `1.2.3`);
  nessun suffisso (`-pre`, `+build`): il validatore li rifiuta con un errore.
- La prima versione di una voce è `1.0.0`; per una bozza volutamente incompleta si può partire da
  `0.1.0`.
- Si incrementa:
  - **MAJOR** quando cambia il comportamento o l'interfaccia in modo incompatibile: input rinominati,
    rimossi o con significato diverso, segnale/plot/valore di ritorno calcolati in modo diverso a
    parità di input, cambio di nome dello studio;
  - **MINOR** quando si aggiunge qualcosa in modo compatibile: nuovi input con default che
    riproducono il comportamento precedente, nuovi plot, nuove opzioni;
  - **PATCH** per correzioni di bug, commenti, riformattazioni, documentazione: a parità di input il
    risultato atteso non cambia (o cambia solo perché prima era sbagliato).
- Ogni cambio di versione: aggiornare `version` e `updated` nel front matter, aggiungere una riga in
  `## Changelog`, aggiornare la riga `Versione:` nell'intestazione del file `.pl`, rigenerare il
  catalogo. Le tre versioni (front matter, `Versione:` nel `.pl`, prima riga del `## Changelog`)
  devono coincidere: se divergono, `build_catalog.py` emette un avviso.
- Se una funzione in `functions/` cambia `MAJOR`, vanno riviste (e ricompilate in MultiCharts) tutte
  le voci che la elencano in `depends_on`.

## 9. Stile del codice PowerLanguage

Regole seguite dall'esempio incluso e attese per ogni nuovo sorgente `.pl`.

**Intestazione.** Ogni file inizia con un blocco di commento `{ ... }` che riporta: Nome, Tipo
(indicatore/strategia/funzione), Versione, Fonte (citazione breve + id della fonte), Descrizione,
Input, Dipendenze, Note. Esempio:

```
{
  Nome:        BLL1992 MA Band
  Tipo:        Indicatore
  Versione:    1.0.0
  Fonte:       Brock, Lakonishok & LeBaron (1992), J. Finance 47(5)
               [1992-brock-lakonishok-lebaron-simple-technical-trading-rules]
  Descrizione: Media breve, media lunga e banda +/- b intorno alla media lunga.
  Input:       ShortLen, LongLen, Band
  Dipendenze:  BLL_MA_Band_Signal
  Note:        Price di default = Close, come nel paper.
}
```

**Struttura.**

- Dichiarare prima `inputs:` poi `variables:`, con valori iniziali per tutte le variabili.
  Usare `intrabarpersist` solo quando serve davvero (valori che devono sopravvivere ai tick
  intra-bar).
- Usare `Close` come input `Price` di default, come nel paper (prezzi di chiusura).
- Proteggersi dalle barre insufficienti: `if CurrentBar > LongLen then begin ... end;` (o
  equivalente) prima di calcolare medie e segnali.
- Codice leggibile: una istruzione per riga, indentazione a 4 spazi, nomi degli input in PascalCase
  (`ShortLen`, `LongLen`, `Band`, `HoldDays`, `AllowShort`).
- Commenti **in italiano** che spiegano la corrispondenza tra il codice e le regole del paper
  (es. `// regola VMA: segnale di acquisto se MA breve > MA lunga * (1 + b)`).

**Indicatori.**

- Plot con `Plot1(valore, "Nome")` … `Plot4(...)`; nomi dei plot parlanti (`"MA breve"`,
  `"Banda sup"`).
- `SetPlotColor` solo se utile (per esempio per colorare il segnale).

**Strategie** (in MultiCharts: *signal*).

- Ordini sempre con nome e `next bar at market`:
  `Buy ("LE") next bar at market;`, `SellShort ("SE") next bar at market;`,
  `Sell ("LX") next bar at market;`, `BuyToCover ("SX") next bar at market;`.
- Periodo di detenzione fisso con `MarketPosition` e `BarsSinceEntry`.
- Non indicare la quantità negli ordini (`Buy 1 contract ...`): la decidono le proprietà della
  strategia in MultiCharts, a meno che un input non la esponga esplicitamente.
- Esporre un input `AllowShort` (true = short sui segnali di vendita, false = flat), perché nei
  paper "sell" spesso significa "fuori dal mercato o short".

**Funzioni.**

- Il valore di ritorno si assegna al nome della funzione (`BLL_MA_Band_Signal = 1;`).
- Input dichiarati con il tipo giusto: `numericseries` per le serie di prezzo, `numericsimple` per
  i parametri scalari (es. `inputs: Price(numericseries), ShortLen(numericsimple);`).
- Gestire i casi limite dichiarati nella scheda (es. `ShortLen = 1` → la media è il prezzo stesso).
- Il nome della funzione, il nome dello studio in MultiCharts e il nome del file `.pl` coincidono.

## 10. PDF, copyright e file grandi

- Il **PDF locale è opzionale**. La scheda `README.md` con riferimento, DOI/URL e note di
  estrazione è il contenuto essenziale della fonte.
- Si carica un PDF solo se la licenza lo consente (open access, preprint con licenza compatibile,
  materiale proprio). **Se non si può ridistribuire, non va caricato**: si lasciano solo `doi` e/o
  `url`, che restano il puntatore ufficiale alla fonte.
- Se il PDF è presente, va dichiarato nel campo `pdf:` (il validatore controlla che il file esista);
  il nome consigliato è `paper.pdf`. Per un PDF tenuto solo in locale **non** si imposta `pdf:`,
  altrimenti il validatore segnala il file mancante.
- **Privacy.** I PDF scaricati dagli editori spesso contengono filigrane (nome, istituzione,
  indirizzo IP, data di download) e metadati personali: prima di caricarne uno controllare e, se
  serve, ripulirlo.
- **La storia di git non si cancella da sola.** Un file committato resta nella storia anche dopo
  `git rm`; rimuoverlo davvero richiede di riscrivere la storia (e di forzare il push). In caso di
  dubbio tenere il PDF fuori dal repository (cartella locale, oppure un Git LFS privato) e lasciare
  nella scheda solo `doi`/`url`.
- `.gitattributes` tratta `*.pdf`, `*.pla`, `*.png`, `*.jpg` e `*.xlsx` come binari. Per file grandi è possibile
  attivare **Git LFS** (opzionale) togliendo il commento alla riga
  `# *.pdf filter=lfs diff=lfs merge=lfs -text` in `.gitattributes` ed eseguendo `git lfs install`
  e `git lfs track "*.pdf"` prima di aggiungere i file.
- Nelle schede si riportano formule, regole e parametri con parole proprie e con la notazione del
  paper; non si copiano porzioni estese di testo.

## 11. Tag

- Minuscoli, kebab-case, in inglese per uniformità con i nomi tecnici (`moving-average`,
  `trend-following`, `breakout`, `mean-reversion`, `volatility`, `technical-analysis`).
- Riutilizzare i tag già presenti nel catalogo prima di inventarne di nuovi.

## 12. Git

- **Rami.** Un ramo per catena logica: `paper/<paper-id>` (fonte + voci derivate) oppure
  `study/<slug>` (una sola voce). Si fa merge su `main` solo con la CI verde. Correzioni piccole
  (refusi, una riga di scheda) possono andare direttamente su `main`.
- **Messaggi di commit.** In italiano, imperativo presente, prima riga ≤ 72 caratteri con uno dei
  prefissi `fonte:`, `funzione:`, `indicatore:`, `strategia:`, `docs:`, `tools:`. Esempio:
  `strategia: aggiungi BLL1992 MA Crossover con HoldDays per VMA/FMA`. Dettagli, se servono, nel
  corpo dopo una riga vuota.
- **Catalogo sempre aggiornato.** Ogni commit che tocca una scheda include `CATALOG.md` e
  `catalog.json` rigenerati; prima del push eseguire `python tools/build_catalog.py --check`.
- **Non riscrivere la storia di `main`** (niente `push --force`, `rebase` o `amend` su commit già
  pubblicati); si corregge con un nuovo commit. Vale anche per i PDF caricati per errore (§10).
