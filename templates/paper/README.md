---
type: {{PAPER_TYPE}}
id: {{ID}}
title: {{TITLE}}
authors: {{AUTHORS}}
year: {{YEAR}}
status: to-read
tags: {{TAGS}}
added: {{DATE}}
doi: {{DOI}}
url: {{URL}}
summary: {{SUMMARY}}
# Opzionali: rimuovere il prefisso "# " per attivare il campo
# journal: Nome della rivista
# volume: 1
# issue: 1
# pages: 1-10
# publisher: Nome dell'editore
# pdf: paper.pdf
# isbn: 978-0000000000
---

# {{TITLE}}

<!-- Scheda della fonte (paper, libro, capitolo, articolo, tesi o pagina web). Aggiornare `status` man mano: to-read, reading, read, extracted. Il PDF, se presente, va nella cartella e nel campo `pdf`; se non è distribuibile, lasciare solo `doi`/`url`. -->

## Riferimento

<!-- Citazione completa in stile APA (autori, anno, titolo, rivista/editore, volume, pagine, DOI o URL). -->

{{CITATION}}

## Sintesi

<!-- 5-10 righe: domanda di ricerca, metodo, risultato principale. Riassumere con parole proprie, non copiare l'abstract. -->

## Idee chiave

<!-- Elenco puntato delle idee riutilizzabili nel codice: segnali, filtri, gestione della posizione, holding period. -->

## Regole / Formule

<!-- Regole operative e formule ESATTAMENTE come nel paper, con la sua notazione; indicare pagina, equazione o tabella. -->

## Parametri usati nel paper

<!-- Un parametro per riga con i valori testati dagli autori (lunghezze, bande, holding period...). -->

| Parametro | Valori nel paper | Note |
|-----------|------------------|------|

## Dati e risultati del paper

<!-- Strumento, periodo, frequenza dei dati, costi di transazione; risultati principali in breve, con pagina o tabella di riferimento. -->

## Note di estrazione

<!-- Cosa era ambiguo nel testo e quali decisioni sono state prese nel tradurre le regole in PowerLanguage (es. prezzo usato, gestione della banda, posizione flat vs short). Se superano ~30 righe, spostare il dettaglio in `notes.md` nella stessa cartella e lasciare qui una sintesi con il link `Note estese: [notes.md](notes.md)`. -->

## Implementazioni in questa libreria

<!-- Link alle voci derivate da questa fonte: il catalogo ricava la mappa dal campo `papers` delle voci e `build_catalog.py` avvisa se qui manca una voce che cita questa fonte. -->
<!-- - [Nome studio](../../indicators/<slug>/README.md) -->
<!-- - [Nome studio](../../strategies/<slug>/README.md) -->
<!-- - [Nome_Funzione](../../functions/<slug>/README.md) -->

## Riferimenti correlati

<!-- Altri paper, libri o articoli collegati (repliche, estensioni, critiche), con DOI o URL se disponibili. -->
