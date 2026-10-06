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

<!-- Una riga sotto il titolo: cosa fa l'indicatore e da quale fonte deriva. -->

## Descrizione

<!-- Cosa misura o visualizza l'indicatore, a cosa serve, in quale contesto (mercati, timeframe, condizioni). -->

## Fonte

<!-- Un punto per ogni id in `papers`, con link alla scheda e il punto esatto del testo da cui deriva il codice: -->
<!-- - [Autore (Anno). Titolo](../../papers/<paper-id>/README.md) — sezione, pagina o equazione. -->

## Logica

<!-- Regole e formule implementate, nella notazione del paper, con la corrispondenza fra simboli del paper e variabili del codice. -->

## Input

<!-- Un input per riga; i default devono coincidere con quelli dichiarati in `{{SOURCE_FILE}}`. -->

| Nome | Tipo | Default | Descrizione |
|------|------|---------|-------------|
| Price | numericseries | Close | Serie di prezzo usata nel calcolo |
| Length | numericsimple | 20 | Periodo di calcolo |

## Output

<!-- Plot prodotti (Plot1..PlotN): nome, significato, eventuale colore o stile consigliato. -->

| Plot | Nome | Descrizione |
|------|------|-------------|
| Plot1 | {{NAME}} | Valore principale dell'indicatore |

## Dipendenze

<!-- Funzioni della libreria richieste (campo `depends_on`), da importare in MultiCharts PRIMA di questo studio; scrivere "Nessuna" se non ce ne sono: -->
<!-- - [Nome_Funzione](../../functions/<slug>/README.md) -->

## Note di implementazione

<!-- Scelte fatte nel tradurre il paper in PowerLanguage: ambiguità risolte, differenze rispetto all'originale, limiti noti. Se superano ~30 righe, spostare il dettaglio in `notes.md` nella stessa cartella e lasciare qui una sintesi con il link `Note estese: [notes.md](notes.md)`. -->

## Test e risultati

<!-- Come è stato verificato: versione MultiCharts (campo `multicharts_version`), strumento, timeframe, periodo, confronto con i risultati del paper. Immagini, export del report e elenchi operazioni vanno nella sottocartella `backtests/` con nome `<AAAA-MM-GG>_<strumento>_<timeframe>_<descrizione>.<ext>` e ogni file va citato qui. -->

## Changelog

<!-- Una riga per versione, dalla più recente: `- AAAA-MM-GG — x.y.z: cosa è cambiato`. Aggiornare anche `version` e `updated` nel front matter. -->

- {{DATE}} — 1.0.0: prima bozza creata dal template.
