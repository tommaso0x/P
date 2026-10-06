# Flusso di lavoro: dal paper al codice testato

Percorso standard per trasformare una fonte in codice PowerLanguage verificato. I comandi si
lanciano dalla radice del repository con Python ≥ 3.10 (nessuna dipendenza). Le convenzioni su
nomi, metadati e stati sono in [CONVENZIONI.md](CONVENZIONI.md); le operazioni nel PowerLanguage
Editor sono in [MULTICHARTS.md](MULTICHARTS.md).

L'esempio usato in ogni passo è la catena inclusa nella libreria: Brock, Lakonishok e LeBaron (1992)
→ funzione `BLL_MA_Band_Signal` → indicatore `BLL1992 MA Band` → strategie `BLL1992 MA Crossover` e
`BLL1992 Trading Range Breakout`.

Suggerimento: ogni comando `new_entry.py` accetta `--dry-run` per vedere cosa verrebbe creato senza
scrivere nulla, e `--date YYYY-MM-DD` per impostare una data diversa da oggi.

## 1. Leggere il paper

Prima lettura completa, segnando: le **regole operative** (quando si compra, quando si vende,
quanto si resta in posizione), le **formule** nella notazione dell'autore, i **parametri** testati,
i **dati** usati (mercato, periodo, frequenza) e le **ipotesi** (costi, short, esecuzione).

## 2. Creare la scheda della fonte

```bash
python tools/new_entry.py paper "Simple Technical Trading Rules and the Stochastic Properties of Stock Returns" \
  --authors "William Brock, Josef Lakonishok, Blake LeBaron" --year 1992 \
  --type paper --doi 10.1111/j.1540-6261.1992.tb04681.x \
  --url https://doi.org/10.1111/j.1540-6261.1992.tb04681.x \
  --tags technical-analysis,moving-average,trading-range-breakout
```

L'identificativo viene derivato automaticamente come
`<anno>-<cognomi di al più 3 autori>-<prime 5 parole del titolo>` senza le parole vuote (*the*,
*and*, *of*, ...): qui `1992-brock-lakonishok-lebaron-simple-technical-trading-rules`. Passare
`--id <id>` quando si vuole un titolo breve diverso. Viene creata `papers/<id>/README.md` dal
template.

Compilare subito `## Riferimento` (citazione APA) e `## Sintesi`; aggiungere i campi opzionali
(`journal`, `volume`, `issue`, `pages`). Stato: `to-read` → `reading` → `read` man mano che la
scheda si completa. Il PDF va aggiunto (campo `pdf:`) solo se può essere ridistribuito; altrimenti
bastano `doi`/`url` (vedi [CONVENZIONI.md §10](CONVENZIONI.md#10-pdf-copyright-e-file-grandi)).

## 3. Scrivere le note di estrazione

Nella scheda della fonte, compilare:

- `## Regole / Formule` — le regole così come le scrive il paper, con la sua notazione (es. per
  BLL 1992: segnale di acquisto se MA breve > MA lunga·(1+b), di vendita se MA breve < MA lunga·(1−b),
  neutro dentro la banda).
- `## Parametri usati nel paper` — tutte le combinazioni testate dagli autori (es. coppie (1,50),
  (1,150), (5,150), (1,200), (2,200); banda b ∈ {0, 0.01}; n ∈ {50, 150, 200}).
- `## Dati e risultati del paper` — dataset, periodo, risultati principali in breve.
- `## Note di estrazione` — ogni **ambiguità** incontrata e la **decisione** presa per il codice:
  "sell" significa flat o short? la media a 1 giorno è il prezzo? il massimo degli ultimi n giorni
  include la barra corrente? quando si esegue l'ordine (chiusura o apertura successiva)? Queste
  decisioni diventano input espliciti (es. `AllowShort`, `HoldDays`) o commenti nel codice.

Al termine lo stato della fonte è `read`.

## 4. Creare la funzione riutilizzabile

Se la regola contiene un calcolo che servirà a più studi (il segnale, una media particolare, un
filtro), si isola in una funzione:

```bash
python tools/new_entry.py function "BLL_MA_Band_Signal" --slug bll-ma-band-signal \
  --paper 1992-brock-lakonishok-lebaron-simple-technical-trading-rules \
  --tags moving-average,signal \
  --summary "Segnale +1/-1/0 della media breve rispetto alla banda intorno alla media lunga."
```

Vengono creati `functions/bll-ma-band-signal/README.md` e
`functions/bll-ma-band-signal/BLL_MA_Band_Signal.pl`. Il nome del file (senza `.pl`) deve coincidere
con il nome della funzione (requisito di MultiCharts; per il validatore è un errore) e iniziare con una lettera o `_`. Per le funzioni il nome passato a `new_entry.py` deve già essere un
identificatore valido (es. `_3_Bar_Reversal`, non `3 Bar Reversal`): il prefisso `_` che
`new_entry.py` antepone al nome del file quando il nome inizia con una cifra vale per indicatori e
strategie, mentre per una funzione renderebbe `source_file` diverso da `name` e `build_catalog.py`
lo segnalerebbe come errore (lo script avvisa già alla creazione). Scrivere il
codice nel `.pl` seguendo lo stile di
[CONVENZIONI.md §9](CONVENZIONI.md#9-stile-del-codice-powerlanguage): input `numericseries` /
`numericsimple`, assegnazione del risultato al nome della funzione, gestione dei casi limite,
commenti in italiano sulla corrispondenza con il paper. Compilare `## Logica`, `## Input`, `## Output`.

## 5. Creare l'indicatore per visualizzare

L'indicatore serve a **vedere** la regola sul grafico prima di automatizzarla:

```bash
python tools/new_entry.py indicator "BLL1992 MA Band" --slug bll1992-ma-band \
  --paper 1992-brock-lakonishok-lebaron-simple-technical-trading-rules \
  --depends bll-ma-band-signal \
  --tags moving-average,trend-following \
  --summary "Media breve, media lunga e banda +/- b come in BLL (1992)."
```

Crea `indicators/bll1992-ma-band/README.md` e `indicators/bll1992-ma-band/BLL1992_MA_Band.pl`.
`--depends` elenca le funzioni richieste (campo `depends_on`): il validatore controlla che esistano
in `functions/`. Plottare le grandezze della regola (media breve, media lunga, banda superiore e
inferiore) e, se utile, il segnale.

## 6. Creare la strategia

```bash
python tools/new_entry.py strategy "BLL1992 MA Crossover" --slug bll1992-ma-crossover \
  --paper 1992-brock-lakonishok-lebaron-simple-technical-trading-rules \
  --depends bll-ma-band-signal \
  --tags moving-average,trend-following \
  --summary "Incrocio di medie con banda; HoldDays=0 (VMA) o >0 (FMA)."

python tools/new_entry.py strategy "BLL1992 Trading Range Breakout" --slug bll1992-trading-range-breakout \
  --paper 1992-brock-lakonishok-lebaron-simple-technical-trading-rules \
  --tags breakout,trading-range \
  --summary "Rottura del massimo/minimo di chiusura degli ultimi Length giorni."
```

Nel `.pl`: ordini `Buy ("LE") next bar at market;`, `SellShort ("SE") next bar at market;`,
`Sell ("LX") next bar at market;`, `BuyToCover ("SX") next bar at market;`; periodo di detenzione
fisso con `MarketPosition` e `BarsSinceEntry`; input `AllowShort`; nessuna quantità negli ordini.
Nella scheda, `## Output` descrive gli ordini generati e `## Note di implementazione` riporta le
decisioni del passo 3.

## 7. Compilare e fare il backtest in MultiCharts

1. Aprire il PowerLanguage Editor e creare gli studi **nell'ordine delle dipendenze**: prima la
   funzione (`File > New > Function`, nome `BLL_MA_Band_Signal`), poi l'indicatore
   (`File > New > Indicator`), poi le strategie (`File > New > Signal`). Incollare il testo di ogni
   `.pl` e compilare (comando `Compile`). Dettagli in [MULTICHARTS.md](MULTICHARTS.md).
2. Applicare l'indicatore a un grafico e verificare a occhio che plot e segnali seguano la regola.
3. Applicare la strategia al grafico, impostare le proprietà (quantità, commissioni, slippage) e
   leggere lo Strategy Performance Report. Confrontare, almeno qualitativamente, con i risultati del
   paper tenendo conto delle differenze (dati, periodo, costi). Nelle proprietà della strategia
   impostare *Maximum number of bars study will reference* (MaxBarsBack) ≥ `LongLen` (o `Length`)
   + 1, es. 201 per le regole con media lunga 200: altrimenti il backtest si interrompe con un
   errore MaxBarsBack (vedi [MULTICHARTS.md](MULTICHARTS.md#maxbarsback)).
4. Salvare nella sottocartella `backtests/` della voce immagini (`*.png`, `*.jpg`), export del
   report (`*.xlsx`, `*.html`) ed elenco operazioni (`*.csv`), con nome
   `<AAAA-MM-GG>_<strumento>_<timeframe>_<descrizione>.<ext>` (es.
   `backtests/2026-10-06_DJIA_daily_vma-1-50-001.png`); eventualmente anche l'archivio `.pla`
   esportato, nella cartella della voce (campo `archive_file`).
5. Compilare `## Test e risultati` nella scheda: versione di MultiCharts (anche nel campo
   `multicharts_version`, atteso per lo stato `tested`), strumento, periodo, parametri, esito, e un
   riferimento a ogni file salvato in `backtests/`.

## 8. Aggiornare stato, versione e changelog

Nel front matter di ogni voce verificata:

- `status: draft` → `tested` (con `multicharts_version` impostato, altrimenti il validatore avvisa);
- `version` secondo semver (la prima versione verificata resta `1.0.0` se nata così; una modifica
  successiva incrementa `PATCH`/`MINOR`/`MAJOR` come da [CONVENZIONI.md §8](CONVENZIONI.md#8-versioning-semver));
- `updated` con la data odierna;
- una riga in `## Changelog`, es. `- 2026-10-06 — 1.0.0: prima versione testata su DJIA daily.`
- la stessa versione nella riga `Versione:` dell'intestazione `{ ... }` del file `.pl`: front
  matter, `.pl` e prima riga del changelog devono coincidere (il validatore avvisa se divergono).

Nella scheda della fonte: `status: read` → `extracted` e link alle voci in
`## Implementazioni in questa libreria` (il validatore avvisa se una voce che cita la fonte non è
elencata lì). Se una voce viene sostituita da un'altra: `status: deprecated` e
`superseded_by: <slug della nuova voce>`.

## 9. Rigenerare il catalogo

```bash
python tools/build_catalog.py            # valida e riscrive CATALOG.md e catalog.json
python tools/build_catalog.py --check    # conferma che tutto è valido e aggiornato (lo stesso controllo della CI)
python -m unittest discover -s tools/tests -v   # test degli strumenti (facoltativo in locale, obbligatorio in CI)
```

Se compaiono righe `ERRORE <percorso>: <messaggio>`, correggere le schede indicate e rilanciare.
Gli avvisi (`AVVISO ...`: fonte senza implementazioni, voce con `papers: []`, `tested`/`stable`
senza `multicharts_version`, versioni divergenti tra front matter, `.pl` e changelog, chiave
sconosciuta nel front matter, voce non elencata in `## Implementazioni in questa libreria` della
fonte che cita, `deprecated` senza `superseded_by`) non bloccano ma segnalano qualcosa da
sistemare. `CATALOG.md` e `catalog.json` non si modificano a mano.

## 10. Commit

```bash
git switch -c paper/1992-brock-lakonishok-lebaron-simple-technical-trading-rules
git add papers/1992-brock-lakonishok-lebaron-simple-technical-trading-rules \
        functions/bll-ma-band-signal indicators/bll1992-ma-band \
        strategies/bll1992-ma-crossover strategies/bll1992-trading-range-breakout \
        CATALOG.md catalog.json
git commit -m "fonte: aggiungi BLL 1992 con funzione segnale, indicatore e strategie"
python tools/build_catalog.py --check && git push -u origin HEAD
```

Includere sempre nel commit il catalogo rigenerato, altrimenti la CI fallisce su
`build_catalog.py --check`. Un ramo e un commit per catena logica (fonte + voci derivate) o per
singola voce rendono la storia leggibile; il merge su `main` si fa con la CI verde. Rami, prefissi
dei messaggi e regole sulla storia sono in
[CONVENZIONI.md §12](CONVENZIONI.md#12-git).

## Riepilogo

| Passo | Risultato | Stato |
|---|---|---|
| 1–2 | `papers/<id>/README.md` con riferimento e sintesi | fonte `to-read` → `reading` |
| 3 | regole, parametri, note di estrazione | fonte `read` |
| 4 | `functions/<slug>/` con `.pl` e scheda | codice `draft` |
| 5 | `indicators/<slug>/` | codice `draft` |
| 6 | `strategies/<slug>/` | codice `draft` |
| 7 | compilazione, grafico, backtest, immagini | — |
| 8 | front matter e changelog aggiornati | codice `tested`, fonte `extracted` |
| 9 | `CATALOG.md` e `catalog.json` rigenerati, `--check` verde | — |
| 10 | commit sul ramo `paper/<id>` o `study/<slug>`, merge su `main` con CI verde | — |
