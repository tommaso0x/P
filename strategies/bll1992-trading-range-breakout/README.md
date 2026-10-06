---
type: strategy
name: BLL1992 Trading Range Breakout
slug: bll1992-trading-range-breakout
version: 1.0.0
status: draft
language: PowerLanguage
source_file: BLL1992_Trading_Range_Breakout.pl
papers: [1992-brock-lakonishok-lebaron-simple-technical-trading-rules]
depends_on: []
tags: [breakout, trading-range, support-resistance, trend-following, band]
created: 2026-10-06
updated: 2026-10-06
markets: [indici azionari]
timeframes: [daily]
summary: Regola TRB di Brock, Lakonishok e LeBaron (1992), breakout del massimo o minimo delle chiusure delle ultime Length barre con banda e holding fisso, ordini next bar at market.
---

# BLL1992 Trading Range Breakout

Strategia che implementa la regola *trading range breakout* (TRB) del paper di Brock, Lakonishok
e LeBaron (1992): acquisto quando la chiusura supera il massimo delle chiusure delle `Length`
barre precedenti di più della banda `b`, vendita quando scende sotto il minimo di più di `b`; la
posizione è tenuta per `HoldDays` barre (10 nel paper).

## Descrizione

Strategia *breakout* su una sola serie di prezzo: resistenza e supporto sono il massimo e il
minimo delle chiusure degli ultimi `Length` giorni, **esclusa** la barra corrente. Il paper testa
tre finestre (`n` = 50, 150, 200) e due bande (`b` = 0, 0,01) per sei regole in tutto, misurando il
rendimento nei 10 giorni successivi al segnale, come per la FMA. I default (`Length = 50`,
`Band = 0.01`, `HoldDays = 10`) corrispondono alla regola TRB `(50, 0.01)`.

Nel paper "sell" significa stare fuori dal mercato oppure short: l'input `AllowShort` sceglie fra
le due letture. Con `HoldDays = 0` la posizione è tenuta fino al segnale opposto: è un'estensione
non testata nel paper. Mercati e timeframe previsti: indici azionari su dati giornalieri.

## Fonte

- [Brock, Lakonishok & LeBaron (1992). Simple Technical Trading Rules and the Stochastic Properties of Stock Returns](../../papers/1992-brock-lakonishok-lebaron-simple-technical-trading-rules/README.md)
  — regola TRB: resistenza e supporto come massimo e minimo delle chiusure degli `n` giorni
  precedenti, banda `b`, holding di 10 giorni; vedi le sezioni *Regole / Formule* e *Parametri
  usati nel paper* della scheda.

## Logica

Notazione del paper: `P_t` chiusura del giorno `t`; `Max_t(n) = max(P_{t-1}, …, P_{t-n})`;
`Min_t(n) = min(P_{t-1}, …, P_{t-n})`; `b` banda.

| Paper | Codice |
|-------|--------|
| `P_t` | `Price` |
| `Max_t(n)` (resistenza) | `Resistance = Highest(Price[1], Length)` |
| `Min_t(n)` (supporto) | `Support = Lowest(Price[1], Length)` |
| buy: `P_t > Max_t(n)·(1 + b)` | `SignalValue = 1` |
| sell: `P_t < Min_t(n)·(1 − b)` | `SignalValue = -1` |

Gestione della posizione:

- da flat (`MarketPosition = 0`): `SignalValue = 1` → `Buy ("LE")`; `SignalValue = -1` e
  `AllowShort` → `SellShort ("SE")`;
- in posizione con `HoldDays > 0` (paper): i segnali sono ignorati; quando
  `BarsSinceEntry(0) >= HoldDays - 1` → `Sell ("LX time")` se long, `BuyToCover ("SX time")` se
  short (eseguiti all'apertura successiva, così la posizione copre `HoldDays` rendimenti giornalieri);
- in posizione con `HoldDays = 0` (estensione): si tiene fino al segnale opposto; da long un
  segnale −1 → `SellShort ("SE")` se `AllowShort` (inversione) altrimenti `Sell ("LX")`; da short
  un segnale +1 → `Buy ("LE")` (inversione).

Tutti gli ordini sono `next bar at market`. Guardia iniziale: `CurrentBar > Length` (servono
`Length` barre precedenti più la corrente).

## Input

| Nome | Tipo | Default | Descrizione |
|------|------|---------|-------------|
| Price | numericseries | Close | Serie di prezzo `P_t`; il paper usa la chiusura giornaliera |
| Length | numericsimple | 50 | Finestra `n` di barre precedenti per massimo e minimo (paper: 50, 150, 200) |
| Band | numericsimple | 0.01 | Banda `b` in frazione (paper: 0 oppure 0.01 = 1 %) |
| HoldDays | numericsimple | 10 | Holding fisso in barre (paper: 10); 0 = posizione tenuta fino al segnale opposto |
| AllowShort | truefalse | true | true = apre short sui segnali di vendita; false = resta flat |

## Output

| Etichetta | Ordine | Condizione |
|-----------|--------|------------|
| LE | Buy next bar at market | Flat e `Price > Resistance·(1 + Band)`; con `HoldDays = 0` anche da short su segnale +1 (inversione) |
| SE | SellShort next bar at market | Flat, `AllowShort = true` e `Price < Support·(1 − Band)`; con `HoldDays = 0` anche da long su segnale −1 (inversione) |
| LX | Sell next bar at market | `HoldDays = 0`, posizione long, segnale −1 e `AllowShort = false` |
| LX time | Sell next bar at market | `HoldDays > 0`, posizione long e `BarsSinceEntry(0) >= HoldDays - 1` |
| SX time | BuyToCover next bar at market | `HoldDays > 0`, posizione short e `BarsSinceEntry(0) >= HoldDays - 1` |

La quantità non è specificata negli ordini: è decisa dalle proprietà della strategia in
MultiCharts.

## Dipendenze

Nessuna: usa solo le funzioni built-in `Highest` e `Lowest` di MultiCharts.

## Note di implementazione

- **Barra corrente esclusa**: `Highest(Price[1], Length)` e `Lowest(Price[1], Length)` guardano
  alle `Length` barre precedenti (la serie è spostata indietro di una barra con `Price[1]`);
  includendo la barra corrente il breakout sarebbe impossibile, perché `Close` non può superare un
  massimo che la contiene (nota 3 della scheda del paper). Si è preferita questa forma a
  `Highest(Price, Length)[1]`, equivalente ma non accettata da tutti i compilatori compatibili con
  EasyLanguage.
- **Timing degli ordini**: segnale sulla chiusura di `t`, esecuzione all'apertura di `t+1`; il
  paper misura i rendimenti close-to-close dal giorno del segnale (nota 1 della scheda del paper).
- **Conteggio dell'holding**: `BarsSinceEntry(0)` vale 0 sulla barra di ingresso (apertura di
  `t+1` per un segnale alla chiusura di `t`). L'ordine di uscita è inviato quando vale
  `HoldDays - 1` ed eseguito all'apertura successiva, cioè all'apertura di `t+1+HoldDays`: la
  posizione copre esattamente `HoldDays` rendimenti giornalieri open-to-open, l'equivalente dei 10
  rendimenti close-to-close del paper. Con `>= HoldDays` la posizione durerebbe un giorno di più.
- **MaxBarsBack**: per le strategie MultiCharts non rileva automaticamente il numero di barre
  storiche necessarie; nelle proprietà della strategia impostare *Maximum number of bars study will
  reference* ≥ `Length + 1` (es. 201 per `Length = 200`), altrimenti il backtest si interrompe con
  un errore di MaxBarsBack.
- **Segnali durante l'holding**: ignorati, come nel paper. Allo scadere la strategia torna flat e
  da lì rientra solo su un nuovo breakout.
- **`HoldDays = 0`**: variante non presente nel paper; il segnale opposto chiude la posizione e, se
  `AllowShort = true`, la inverte in un solo ordine (comportamento standard di MultiCharts per
  `Buy` da short e `SellShort` da long).
- **Banda moltiplicativa**: `Max·(1 + b)` e `Min·(1 − b)`, con `b` in frazione; usare `Band >= 0`.
  Se entrambe le condizioni fossero vere (impossibile con `Band >= 0`, perché
  `Max >= Min`) prevale il segnale −1, assegnato per ultimo.
- **Costi di transazione e slippage**: assenti nel paper e nel codice; impostarli nelle proprietà
  della strategia (nota 7 della scheda del paper).

## Test e risultati

Stato `draft`: il codice **non è ancora stato compilato né sottoposto a backtest in MultiCharts**.
Prima di passare a `tested`:

1. compilare la strategia in PowerLanguage Editor e applicarla a un indice azionario con dati
   giornalieri (es. Dow Jones Industrial Average), senza costi e con quantità fissa;
2. verificare su alcune operazioni che l'ingresso avvenga solo quando la chiusura supera di più
   dell'1 % il massimo (o il minimo) delle 50 chiusure precedenti, ricalcolato a mano o in un
   foglio di calcolo;
3. con `HoldDays = 10` controllare sul report delle operazioni che ogni trade esca all'apertura
   della decima barra dopo l'ingresso (10 rendimenti giornalieri) e che i segnali durante l'holding
   siano ignorati;
4. con `HoldDays = 0` e `AllowShort = true` verificare le inversioni long/short;
5. confrontare il segno dei rendimenti medi dopo i segnali buy e sell con i risultati del paper
   (buy > sell, sell negativi), tenendo conto che i dati e il periodo saranno diversi.

## Changelog

- 2026-10-06 — 1.0.0: prima versione (bozza) della regola TRB con holding fisso e variante
  `HoldDays = 0`; non ancora compilata in MultiCharts.
