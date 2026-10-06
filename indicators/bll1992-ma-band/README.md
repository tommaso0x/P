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
tags: [moving-average, band, trend-following, overlay]
created: 2026-10-06
updated: 2026-10-06
markets: [indici azionari]
timeframes: [daily]
summary: Media breve, media lunga e bande (1 ± b) delle regole di media mobile di Brock, Lakonishok e LeBaron (1992), con la media breve colorata dal segnale +1 / -1 / 0.
---

# BLL1992 MA Band

Indicatore che disegna sul grafico dei prezzi gli elementi delle regole di media mobile del paper
di Brock, Lakonishok e LeBaron (1992): media breve `MA(s)`, media lunga `MA(l)` e le due bande
`MA(l)·(1 ± b)`; la media breve è colorata in base al segnale della funzione
`BLL_MA_Band_Signal` (verde = acquisto, rosso = vendita, grigio = neutrale).

## Descrizione

L'indicatore serve a **vedere** le regole VMA e FMA del paper prima di metterle in una strategia:
mostra quando la media breve esce dalla banda intorno alla media lunga e quindi quando le strategie
[BLL1992 MA Crossover](../../strategies/bll1992-ma-crossover/README.md) generano i segnali. Con i
default (`ShortLen = 1`, `LongLen = 50`, `Band = 0.01`) riproduce la regola `MA(1, 50, 0.01)` del
paper: la "media breve" è il prezzo di chiusura stesso.

Contesto previsto: indici azionari su dati giornalieri (il paper usa le chiusure del Dow Jones
Industrial Average 1897–1986); l'indicatore funziona su qualunque strumento e timeframe, ma i
parametri del paper sono stati scelti per il giornaliero.

## Fonte

- [Brock, Lakonishok & LeBaron (1992). Simple Technical Trading Rules and the Stochastic Properties of Stock Returns](../../papers/1992-brock-lakonishok-lebaron-simple-technical-trading-rules/README.md)
  — regole di media mobile con banda `b` e coppie `(s, l)` testate; vedi le sezioni *Regole /
  Formule* e *Parametri usati nel paper* della scheda.

## Logica

Notazione del paper: `P_t` chiusura del giorno `t`; `MA_t(k)` media mobile semplice a `k` giorni;
`s` e `l` lunghezze delle medie; `b` banda.

| Paper | Codice | Plot |
|-------|--------|------|
| `MA_t(s)` (= `P_t` se `s = 1`) | `ShortMA` | Plot1 "MA breve" |
| `MA_t(l)` | `LongMA` | Plot2 "MA lunga" |
| `MA_t(l) · (1 + b)` | `UpperBand` | Plot3 "Banda sup" |
| `MA_t(l) · (1 − b)` | `LowerBand` | Plot4 "Banda inf" |
| segnale buy / sell / neutro | `SignalValue = BLL_MA_Band_Signal(Price, ShortLen, LongLen, Band)` | colore di Plot1 |

Regola del paper: segnale di acquisto se `MA(s) > MA(l)·(1 + b)`, di vendita se
`MA(s) < MA(l)·(1 − b)`, nessun segnale dentro la banda. I calcoli iniziano dalla barra `LongLen`
(guardia `CurrentBar >= LongLen`).

## Input

| Nome | Tipo | Default | Descrizione |
|------|------|---------|-------------|
| Price | numericseries | Close | Serie di prezzo `P_t`; il paper usa la chiusura giornaliera |
| ShortLen | numericsimple | 1 | Lunghezza `s` della media breve (paper: 1, 2, 5); con 1 la media coincide con il prezzo |
| LongLen | numericsimple | 50 | Lunghezza `l` della media lunga (paper: 50, 150, 200) |
| Band | numericsimple | 0.01 | Banda `b` in frazione (paper: 0 oppure 0.01 = 1 %) |

## Output

| Plot | Nome | Descrizione |
|------|------|-------------|
| Plot1 | MA breve | `MA(s)`; colore verde se segnale +1, rosso se −1, grigio scuro se 0 (`SetPlotColor`) |
| Plot2 | MA lunga | `MA(l)` |
| Plot3 | Banda sup | `MA(l)·(1 + b)`: soglia del segnale di acquisto |
| Plot4 | Banda inf | `MA(l)·(1 − b)`: soglia del segnale di vendita |

Tutti i plot sono in unità di prezzo: applicare l'indicatore **sul grafico dei prezzi** (scala
dello strumento), non in un sottografico separato.

## Dipendenze

- [BLL_MA_Band_Signal](../../functions/bll-ma-band-signal/README.md) — da importare in MultiCharts
  **prima** di questo indicatore.

## Note di implementazione

- Le medie sono ricalcolate nell'indicatore (servono per i plot) e il segnale è chiesto alla
  funzione condivisa: il doppio calcolo di `Average` è trascurabile e garantisce che il colore
  coincida con il segnale usato dalle strategie.
- `ShortLen <= 1` → `ShortMA = Price`, come nel paper con `s = 1` (nota 6 della scheda del paper).
- La banda è moltiplicativa (`MA(l)·(1 ± b)`), con `b` in frazione; con `Band = 0` Plot2, Plot3 e
  Plot4 coincidono.
- Colori con `SetPlotColor(1, ...)`: `Green` (+1), `Red` (−1), `DarkGray` (0). Stile e spessore
  dei plot si impostano nelle proprietà dell'indicatore.
- Non è previsto un quinto plot numerico del segnale: per vederlo come istogramma in un
  sottografico basta aggiungere `Plot5(SignalValue, "Segnale")` (variante futura).
- Guardia `CurrentBar >= LongLen`: prima di quella barra non viene disegnato nulla (nota 8 della
  scheda del paper).

## Test e risultati

Stato `draft`: il codice **non è ancora stato compilato né verificato in MultiCharts**. Prima di
passare a `tested`:

1. importare la funzione `BLL_MA_Band_Signal`, poi compilare l'indicatore in PowerLanguage Editor;
2. applicarlo su un indice azionario con dati giornalieri (es. Dow Jones) e verificare che con
   `ShortLen = 1` Plot1 coincida con la chiusura e che Plot2 coincida con una media semplice a 50;
3. verificare che Plot3 e Plot4 stiano all'1 % sopra e sotto Plot2 e che il colore di Plot1 cambi
   esattamente quando la chiusura attraversa le bande;
4. salvare uno screenshot (`*.png`) nella cartella e aggiornare questa sezione con versione
   MultiCharts, strumento e periodo.

## Changelog

- 2026-10-06 — 1.0.0: prima versione (bozza) con i quattro plot e la colorazione del segnale; non
  ancora compilata in MultiCharts.
