---
type: function
name: BLL_MA_Band_Signal
slug: bll-ma-band-signal
version: 1.0.0
status: draft
language: PowerLanguage
source_file: BLL_MA_Band_Signal.pl
papers: [1992-brock-lakonishok-lebaron-simple-technical-trading-rules]
depends_on: []
tags: [moving-average, band, signal, trend-following]
created: 2026-10-06
updated: 2026-10-06
summary: Segnale +1 / -1 / 0 dal confronto tra media mobile breve e media lunga con banda percentuale, nucleo delle regole VMA e FMA di Brock, Lakonishok e LeBaron (1992).
---

# BLL_MA_Band_Signal

Funzione PowerLanguage che calcola il segnale di media mobile con banda del paper di Brock,
Lakonishok e LeBaron (1992): **+1** quando la media breve supera la banda superiore della media
lunga, **−1** quando scende sotto la banda inferiore, **0** quando resta dentro la banda. In
MultiCharts il nome della funzione deve coincidere con il nome dello studio e con il nome del file
`BLL_MA_Band_Signal.pl` (senza estensione).

## Descrizione

Tutte le regole di media mobile del paper (10 regole VMA e 10 regole FMA) condividono lo stesso
confronto: media breve `MA(s)` contro media lunga `MA(l)` allargata di una banda `b`. La funzione
isola questo confronto in un unico punto, così che l'indicatore [BLL1992 MA Band](../../indicators/bll1992-ma-band/README.md)
e la strategia [BLL1992 MA Crossover](../../strategies/bll1992-ma-crossover/README.md) usino
esattamente la stessa definizione del segnale e che una correzione si propaghi a entrambi.

Casi limite gestiti:

- `ShortLen <= 1`: la media breve coincide con il prezzo (`MA(1) = P_t`), come nel paper quando
  `s = 1`.
- barre insufficienti (`CurrentBar < LongLen`): la funzione restituisce 0 (nessun segnale).

## Fonte

- [Brock, Lakonishok & LeBaron (1992). Simple Technical Trading Rules and the Stochastic Properties of Stock Returns](../../papers/1992-brock-lakonishok-lebaron-simple-technical-trading-rules/README.md)
  — definizione delle regole di media mobile VMA/FMA con banda `b` e notazione `MA(s, l, b)`;
  vedi la sezione *Regole / Formule* della scheda.

## Logica

Notazione del paper: `P_t` prezzo di chiusura del giorno `t`; `MA_t(k) = (1/k) · Σ_{i=0}^{k-1} P_{t-i}`
media mobile semplice a `k` giorni; `s < l` lunghezze delle medie; `b` banda (0 oppure 0,01).

| Paper | Codice |
|-------|--------|
| `P_t` | `Price` |
| `MA_t(s)` | `ShortMA = Average(Price, ShortLen)`; se `ShortLen <= 1` allora `ShortMA = Price` |
| `MA_t(l)` | `LongMA = Average(Price, LongLen)` |
| `MA_t(l) · (1 + b)` | `UpperBand = LongMA * (1 + Band)` |
| `MA_t(l) · (1 − b)` | `LowerBand = LongMA * (1 - Band)` |

Valore restituito:

- `+1` se `ShortMA > UpperBand` (segnale di acquisto del paper);
- `−1` se `ShortMA < LowerBand` (segnale di vendita del paper);
- `0` altrimenti (media breve dentro la banda: posizione neutra; con `Band = 0` accade solo in
  caso di uguaglianza esatta);
- `0` finché `CurrentBar < LongLen`.

## Input

Le funzioni PowerLanguage non hanno valori di default: la colonna indica i valori usati nel paper.

| Nome | Tipo | Default | Descrizione |
|------|------|---------|-------------|
| Price | numericseries | — (consigliato Close) | Serie di prezzo `P_t`; il paper usa la chiusura giornaliera |
| ShortLen | numericsimple | — (paper: 1, 2, 5) | Lunghezza `s` della media breve; con 1 la media coincide con il prezzo |
| LongLen | numericsimple | — (paper: 50, 150, 200) | Lunghezza `l` della media lunga |
| Band | numericsimple | — (paper: 0 oppure 0.01) | Banda `b` espressa in frazione (0.01 = 1 %), non in percentuale |

## Output

| Tipo di ritorno | Valori | Descrizione |
|-----------------|--------|-------------|
| Numeric | +1, −1, 0 | +1 = media breve sopra la banda superiore (buy); −1 = sotto la banda inferiore (sell); 0 = dentro la banda oppure barre insufficienti |

## Dipendenze

Nessuna: usa solo la funzione built-in `Average` di MultiCharts.

## Note di implementazione

- **Creazione in PowerLanguage Editor**: nuova funzione con nome `BLL_MA_Band_Signal`, tipo di
  ritorno *Numeric*, Function Storage *Series* (oppure *Auto-detect*): così gli studi chiamanti
  possono riferirsi ai valori passati con `BLL_MA_Band_Signal(...)[n]`. Il risultato è assegnato al
  nome della funzione nell'ultima riga.
- **`ShortLen = 1`**: `Average(Price, 1)` restituirebbe comunque il prezzo, ma il caso è gestito in
  modo esplicito per non dipendere dal comportamento della funzione built-in (nota 6 della scheda
  del paper).
- **Banda moltiplicativa**: la banda è applicata alla media lunga come `MA(l) · (1 ± b)`, con `b`
  in frazione; la funzione non valida l'input, usare `Band >= 0` (con banda negativa le due soglie
  si invertirebbero e il codice darebbe la precedenza al segnale +1).
- **`s < l`** non è controllato: con `ShortLen >= LongLen` il risultato è calcolato ma non
  corrisponde a nessuna regola del paper.
- **Barre insufficienti**: guardia `CurrentBar >= LongLen` (nota 8 della scheda del paper); prima
  di quella barra il valore è 0.
- Il segnale è uno **stato** (dove si trova la media breve rispetto alla banda), non un evento di
  incrocio: la distinzione è gestita dalla strategia chiamante.

## Test e risultati

Stato `draft`: il codice **non è ancora stato compilato né verificato in MultiCharts**. Prima di
passare a `tested`:

1. compilare la funzione in PowerLanguage Editor e verificare nome, tipo di ritorno e storage;
2. con `ShortLen = 1`, `LongLen = 50`, `Band = 0` su dati giornalieri, confrontare il segnale con il
   segno di `Close - Average(Close, 50)` calcolato in un foglio di calcolo;
3. con `Band = 0.01` verificare che il segnale valga 0 quando `Close` è entro ±1 % dalla media lunga;
4. verificare che il valore sia 0 sulle prime `LongLen - 1` barre e che il segnale coincida con la
   colorazione dell'indicatore BLL1992 MA Band.

## Changelog

- 2026-10-06 — 1.0.0: prima versione (bozza) estratta dalle regole VMA/FMA di Brock, Lakonishok e
  LeBaron (1992); non ancora compilata in MultiCharts.
