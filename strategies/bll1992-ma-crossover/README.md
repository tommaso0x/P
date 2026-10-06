---
type: strategy
name: BLL1992 MA Crossover
slug: bll1992-ma-crossover
version: 1.0.0
status: draft
language: PowerLanguage
source_file: BLL1992_MA_Crossover.pl
papers: [1992-brock-lakonishok-lebaron-simple-technical-trading-rules]
depends_on: [bll-ma-band-signal]
tags: [moving-average, trend-following, vma, fma, band]
created: 2026-10-06
updated: 2026-10-06
markets: [indici azionari]
timeframes: [daily]
summary: Regole di media mobile VMA (HoldDays = 0) e FMA (HoldDays > 0) di Brock, Lakonishok e LeBaron (1992), con banda e opzione short, ordini next bar at market.
---

# BLL1992 MA Crossover

Strategia che implementa le regole di media mobile del paper di Brock, Lakonishok e LeBaron (1992):
con `HoldDays = 0` la variante a lunghezza variabile (**VMA**), in cui la posizione segue il
segnale barra per barra; con `HoldDays > 0` la variante a lunghezza fissa (**FMA**), in cui si
entra solo quando il segnale cambia (incrocio) e la posizione è tenuta per un numero fisso di barre
ignorando i segnali intermedi.

## Descrizione

Strategia *trend following* su una sola serie di prezzo. Il segnale è quello della funzione
[BLL_MA_Band_Signal](../../functions/bll-ma-band-signal/README.md): +1 quando la media breve
`MA(s)` supera `MA(l)·(1 + b)`, −1 quando scende sotto `MA(l)·(1 − b)`, 0 dentro la banda. I
default (`ShortLen = 1`, `LongLen = 50`, `Band = 0.01`, `HoldDays = 0`) corrispondono alla regola
VMA `(1, 50, 0.01)` del paper; con `HoldDays = 10` si ottiene la FMA con lo stesso holding del
paper.

Nel paper "sell" significa stare fuori dal mercato oppure short: l'input `AllowShort` sceglie fra
le due letture (`true` = short, `false` = flat). Mercati e timeframe previsti: indici azionari su
dati giornalieri, come il Dow Jones Industrial Average 1897–1986 usato nel paper.

## Fonte

- [Brock, Lakonishok & LeBaron (1992). Simple Technical Trading Rules and the Stochastic Properties of Stock Returns](../../papers/1992-brock-lakonishok-lebaron-simple-technical-trading-rules/README.md)
  — regole VMA e FMA, coppie `(s, l)` ∈ {(1, 50), (1, 150), (5, 150), (1, 200), (2, 200)}, banda
  `b` ∈ {0, 0.01}, holding FMA di 10 giorni; vedi le sezioni *Regole / Formule* e *Parametri usati
  nel paper* della scheda.

## Logica

Segnale (identico per le due varianti, calcolato alla chiusura della barra `t`):

| Paper | Codice |
|-------|--------|
| buy: `MA_t(s) > MA_t(l)·(1 + b)` | `SignalValue = 1` |
| sell: `MA_t(s) < MA_t(l)·(1 − b)` | `SignalValue = -1` |
| dentro la banda: nessun segnale | `SignalValue = 0` |

**VMA (`HoldDays = 0`)** — parafrasi della regola del paper: la posizione cambia ogni volta che il
segnale cambia, cioè replica lo stato del segnale a ogni barra:

- `SignalValue = 1` e posizione non long → `Buy ("LE")` (da short il `Buy` inverte la posizione);
- `SignalValue = -1`: se `AllowShort` e posizione non short → `SellShort ("SE")` (da long inverte);
  se non `AllowShort` e posizione long → `Sell ("LX")` (si resta flat);
- `SignalValue = 0` (dentro la banda, posizione neutra) → `Sell ("LX")` se long,
  `BuyToCover ("SX")` se short.

**FMA (`HoldDays > 0`)** — parafrasi della regola del paper: il segnale nasce quando la media
breve attraversa la media lunga (con banda: quando esce dalla banda); dopo il segnale la posizione è
tenuta per 10 giorni fissi e gli altri segnali in quella finestra sono ignorati:

- da flat (`MarketPosition = 0`) si entra solo quando il segnale **cambia** (incrocio):
  `SignalValue = 1` e `SignalValue[1] <> 1` → `Buy ("LE")`; `SignalValue = -1`,
  `SignalValue[1] <> -1` e `AllowShort` → `SellShort ("SE")`. Se `MA(s)` è già fuori dalla banda
  senza un nuovo incrocio non si entra;
- in posizione: i segnali sono ignorati; quando `BarsSinceEntry(0) >= HoldDays - 1` →
  `Sell ("LX time")` se long, `BuyToCover ("SX time")` se short (eseguiti all'apertura
  successiva, così la posizione copre esattamente `HoldDays` rendimenti giornalieri).

Tutti gli ordini sono `next bar at market`. Guardia iniziale: `CurrentBar >= LongLen`.

## Input

| Nome | Tipo | Default | Descrizione |
|------|------|---------|-------------|
| Price | numericseries | Close | Serie di prezzo `P_t`; il paper usa la chiusura giornaliera |
| ShortLen | numericsimple | 1 | Lunghezza `s` della media breve (paper: 1, 2, 5); con 1 la media coincide con il prezzo |
| LongLen | numericsimple | 50 | Lunghezza `l` della media lunga (paper: 50, 150, 200) |
| Band | numericsimple | 0.01 | Banda `b` in frazione (paper: 0 oppure 0.01 = 1 %) |
| HoldDays | numericsimple | 0 | 0 = VMA (posizione segue il segnale); > 0 = FMA con holding fisso di `HoldDays` barre (paper: 10) |
| AllowShort | truefalse | true | true = apre short sui segnali di vendita; false = chiude il long e resta flat |

## Output

| Etichetta | Ordine | Condizione |
|-----------|--------|------------|
| LE | Buy next bar at market | VMA: segnale +1 e posizione non long (da short inverte). FMA: da flat, segnale +1 appena comparso (`SignalValue[1] <> 1`) |
| SE | SellShort next bar at market | VMA: segnale −1, `AllowShort = true`, posizione non short (da long inverte). FMA: da flat, segnale −1 appena comparso (`SignalValue[1] <> -1`) con `AllowShort = true` |
| LX | Sell next bar at market | VMA: posizione long e segnale −1 con `AllowShort = false`, oppure segnale 0 |
| SX | BuyToCover next bar at market | VMA: posizione short e segnale 0 |
| LX time | Sell next bar at market | FMA: posizione long e `BarsSinceEntry(0) >= HoldDays - 1` |
| SX time | BuyToCover next bar at market | FMA: posizione short e `BarsSinceEntry(0) >= HoldDays - 1` |

La quantità non è specificata negli ordini: è decisa dalle proprietà della strategia in
MultiCharts.

## Dipendenze

- [BLL_MA_Band_Signal](../../functions/bll-ma-band-signal/README.md) — da importare in MultiCharts
  **prima** di questa strategia.

## Note di implementazione

- **Timing degli ordini**: il segnale è valutato sulla chiusura della barra `t` e l'ordine
  `next bar at market` è eseguito all'apertura di `t+1`; il paper attribuisce al segnale il
  rendimento close-to-close del giorno `t+1`. La differenza (open-to-close invece di
  close-to-close) è piccola sul giornaliero ma esiste (nota 1 della scheda del paper).
- **Inversioni**: in MultiCharts un `Buy` con posizione short chiude lo short e apre il long in un
  solo ordine (e un `SellShort` da long fa l'opposto); la VMA sfrutta questo comportamento.
- **Conteggio dell'holding FMA**: `BarsSinceEntry(0)` vale 0 sulla barra di ingresso (apertura di
  `t+1` per un segnale alla chiusura di `t`). L'ordine di uscita è inviato quando vale
  `HoldDays - 1` ed eseguito all'apertura successiva, cioè all'apertura di `t+1+HoldDays`: la
  posizione copre esattamente `HoldDays` rendimenti giornalieri open-to-open, l'equivalente dei 10
  rendimenti close-to-close `P_t → P_{t+10}` del paper. Con `>= HoldDays` la posizione durerebbe un
  giorno di più.
- **Ingresso FMA su incrocio, non su stato**: la funzione restituisce dove si trova `MA(s)`
  rispetto alla banda (uno *stato*). Nella FMA si entra solo quando lo stato cambia
  (`SignalValue[1] <> SignalValue`), come nel paper, dove il segnale nasce dall'*attraversamento*
  della banda. Così, allo scadere dell'holding, la strategia non rientra finché non si verifica un
  nuovo incrocio; gli incroci avvenuti durante l'holding sono ignorati e non vengono recuperati.
  Nella VMA, invece, conta lo stato: la posizione segue il segnale barra per barra.
- **MaxBarsBack**: per le strategie MultiCharts non rileva automaticamente il numero di barre
  storiche necessarie; nelle proprietà della strategia impostare *Maximum number of bars study will
  reference* ≥ `LongLen + 1` (es. 201 per `LongLen = 200`), altrimenti il backtest si interrompe
  con un errore di MaxBarsBack.
- **`AllowShort = false`** nella VMA: il segnale −1 chiude il long e lascia flat; il segnale 0 fa
  lo stesso. Con `Band = 0` il segnale 0 compare solo in caso di uguaglianza esatta fra le medie.
- **Costi di transazione e slippage**: assenti nel paper e nel codice; impostarli nelle proprietà
  della strategia per un backtest realistico (nota 7 della scheda del paper).
- **Guardia** `CurrentBar >= LongLen`: coerente con la funzione, che prima restituisce 0.

## Test e risultati

Stato `draft`: il codice **non è ancora stato compilato né sottoposto a backtest in MultiCharts**.
Prima di passare a `tested`:

1. importare la funzione `BLL_MA_Band_Signal`, compilare la strategia e applicarla a un indice
   azionario con dati giornalieri (es. Dow Jones Industrial Average), senza costi e con quantità
   fissa;
2. VMA (`HoldDays = 0`, `Band = 0`): verificare che la strategia sia sempre in posizione (long o
   short con `AllowShort = true`) e che i cambi di posizione coincidano con i cambi di colore
   dell'indicatore BLL1992 MA Band;
3. VMA (`Band = 0.01`): verificare che dentro la banda la posizione venga chiusa;
4. FMA (`HoldDays = 10`): controllare sul report delle operazioni che ogni trade entri all'apertura
   della barra successiva a un incrocio, esca all'apertura della decima barra dopo l'ingresso
   (10 rendimenti giornalieri) e che i segnali intermedi siano ignorati;
5. confrontare il segno dei rendimenti medi dopo i segnali buy e sell con i risultati del paper
   (buy > sell, sell negativi), tenendo conto che i dati e il periodo saranno diversi.

## Changelog

- 2026-10-06 — 1.0.0: prima versione (bozza) con varianti VMA/FMA selezionate da `HoldDays` e
  input `AllowShort`; non ancora compilata in MultiCharts.
