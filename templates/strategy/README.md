---
type: {{TYPE}}
name: {{NAME}}
slug: {{SLUG}}
version: 1.0.0
status: draft
language: PowerLanguage
source_file: {{SOURCE_FILE}}
papers: {{PAPERS}}
depends_on: {{DEPENDS_ON}}
tags: {{TAGS}}
created: {{DATE}}
updated: {{DATE}}
summary: {{SUMMARY}}
# Opzionali: rimuovere il prefisso "# " per attivare il campo
# archive_file: Nome_Studio.pla
# multicharts_version: "14"
# markets: [indici azionari]
# timeframes: [daily]
# author: nome-utente
# superseded_by: slug-della-voce-che-sostituisce-questa (richiesto se status: deprecated)
---

# {{NAME}}

<!-- Una riga sotto il titolo: che cosa fa la strategia e da quale fonte deriva. -->

## Descrizione

<!-- Idea di trading, tipo di strategia (trend following, mean reversion, breakout...), mercati e timeframe previsti. -->

## Fonte

<!-- Un punto per ogni id in `papers`, con link alla scheda e il punto esatto del testo da cui derivano le regole: -->
<!-- - [Autore (Anno). Titolo](../../papers/<paper-id>/README.md) — sezione, pagina o tabella. -->

## Logica

<!-- Regole di ingresso, di uscita e di gestione della posizione, nella notazione del paper, con la corrispondenza alle variabili del codice. -->

## Input

<!-- Un input per riga; i default devono coincidere con quelli dichiarati in `{{SOURCE_FILE}}`. -->

| Nome | Tipo | Default | Descrizione |
|------|------|---------|-------------|
| Price | numericseries | Close | Serie di prezzo usata per il segnale |
| Length | numericsimple | 20 | Periodo di calcolo |
| AllowShort | truefalse | true | true = apre short sui segnali di vendita; false = resta flat |

## Output

<!-- Ordini generati: etichetta usata nel codice, tipo di ordine e condizione che lo attiva. -->

| Etichetta | Ordine | Condizione |
|-----------|--------|------------|
| LE | Buy next bar at market | Segnale long |
| LX | Sell next bar at market | Segnale short con posizione long aperta (chiude il long; con AllowShort = true segue SE) |
| SE | SellShort next bar at market | Segnale short con AllowShort = true |
| SX | BuyToCover next bar at market | Segnale long con posizione short aperta |

## Dipendenze

<!-- Funzioni della libreria richieste (campo `depends_on`), da importare in MultiCharts PRIMA di questo studio; scrivere "Nessuna" se non ce ne sono: -->
<!-- - [Nome_Funzione](../../functions/<slug>/README.md) -->

## Note di implementazione

<!-- Scelte fatte nel tradurre il paper in PowerLanguage: costi di transazione, dimensione della posizione, holding period, ambiguità risolte, differenze rispetto all'originale. Se superano ~30 righe, spostare il dettaglio in `notes.md` nella stessa cartella e lasciare qui una sintesi con il link `Note estese: [notes.md](notes.md)`. -->

## Test e risultati

<!-- Backtest: versione MultiCharts (campo `multicharts_version`), strumento, timeframe, periodo, impostazioni della strategia (incluso MaxBarsBack), metriche principali e confronto con il paper. Immagini, export del report e elenchi operazioni vanno nella sottocartella `backtests/` con nome `<AAAA-MM-GG>_<strumento>_<timeframe>_<descrizione>.<ext>` e ogni file va citato qui. -->

## Changelog

<!-- Una riga per versione, dalla più recente: `- AAAA-MM-GG — x.y.z: cosa è cambiato`. Aggiornare anche `version` e `updated` nel front matter. -->

- {{DATE}} — 1.0.0: prima bozza creata dal template.
