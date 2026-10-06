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
# archive_file: Nome_Funzione.pla
# multicharts_version: "14"
# markets: [indici azionari]
# timeframes: [daily]
# author: nome-utente
# superseded_by: slug-della-voce-che-sostituisce-questa (richiesto se status: deprecated)
---

# {{NAME}}

<!-- Una riga sotto il titolo: che cosa calcola la funzione e da quale fonte deriva. In MultiCharts il nome della funzione deve iniziare con una lettera o con `_` (non con una cifra) e coincidere con il nome dello studio e con il nome del file sorgente senza estensione: `name` e `source_file` diversi sono un errore per `build_catalog.py`. -->

## Descrizione

<!-- Cosa calcola la funzione, perché è stata isolata (riuso fra indicatori e strategie), eventuali casi limite gestiti. -->

## Fonte

<!-- Un punto per ogni id in `papers`, con link alla scheda e il punto esatto del testo da cui deriva la formula: -->
<!-- - [Autore (Anno). Titolo](../../papers/<paper-id>/README.md) — sezione, pagina o equazione. -->

## Logica

<!-- Formula implementata, nella notazione del paper, con la corrispondenza fra simboli del paper e input/variabili della funzione. -->

## Input

<!-- Un input per riga, con il tipo dichiarato in PowerLanguage (numericseries, numericsimple, truefalsesimple...); le funzioni non hanno default: indicare il valore consigliato. -->

| Nome | Tipo | Default | Descrizione |
|------|------|---------|-------------|
| Price | numericseries | — (consigliato Close) | Serie di prezzo su cui calcolare |
| Length | numericsimple | — (consigliato 20) | Periodo di calcolo |

## Output

<!-- Valore di ritorno: tipo (Numeric, TrueFalse...), significato, intervallo dei valori e valore restituito quando le barre sono insufficienti. -->

| Tipo di ritorno | Valori | Descrizione |
|-----------------|--------|-------------|
| Numeric | qualunque (0 se barre insufficienti) | Valore calcolato dalla funzione |

## Dipendenze

<!-- Altre funzioni della libreria richieste (campo `depends_on`), da importare PRIMA di questa; scrivere "Nessuna" se usa solo funzioni built-in: -->
<!-- - [Nome_Funzione](../../functions/<slug>/README.md) -->

## Note di implementazione

<!-- Scelte fatte nel tradurre la formula in PowerLanguage: casi limite (es. Length = 1), tipo Series/Simple impostato nelle proprietà della funzione, differenze rispetto al paper. Se superano ~30 righe, spostare il dettaglio in `notes.md` nella stessa cartella e lasciare qui una sintesi con il link `Note estese: [notes.md](notes.md)`. -->

## Test e risultati

<!-- Come è stata verificata: confronto con valori calcolati a mano o con un foglio di calcolo, versione MultiCharts (campo `multicharts_version`), strumento e periodo usati. Immagini, export del report e elenchi operazioni vanno nella sottocartella `backtests/` con nome `<AAAA-MM-GG>_<strumento>_<timeframe>_<descrizione>.<ext>` e ogni file va citato qui. -->

## Changelog

<!-- Una riga per versione, dalla più recente: `- AAAA-MM-GG — x.y.z: cosa è cambiato`. Aggiornare anche `version` e `updated` nel front matter. -->

- {{DATE}} — 1.0.0: prima bozza creata dal template.
