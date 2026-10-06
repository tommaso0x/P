# Catalogo della libreria

<!-- FILE GENERATO AUTOMATICAMENTE da tools/build_catalog.py: non modificare a mano. -->

> **File generato automaticamente** da `tools/build_catalog.py` a partire dai front matter dei `README.md`: non modificarlo a mano, le modifiche andrebbero perse.
> Per rigenerarlo: `python tools/build_catalog.py` — per verificarlo: `python tools/build_catalog.py --check`.

## Riepilogo

| Tipo | Voci |
|---|---:|
| Indicatori | 1 |
| Strategie | 2 |
| Funzioni | 1 |
| Fonti | 1 |

## Indicatori

| Nome | Slug | Versione | Stato | MC | Fonti | Dipendenze | Tag |
|---|---|---|---|---|---|---|---|
| [BLL1992 MA Band](indicators/bll1992-ma-band/README.md) | `bll1992-ma-band` | 1.0.0 | draft | — | [1992-brock-lakonishok-lebaron-simple-technical-trading-rules](papers/1992-brock-lakonishok-lebaron-simple-technical-trading-rules/README.md) | [bll-ma-band-signal](functions/bll-ma-band-signal/README.md) | moving-average, band, trend-following, overlay |

## Strategie

| Nome | Slug | Versione | Stato | MC | Fonti | Dipendenze | Tag |
|---|---|---|---|---|---|---|---|
| [BLL1992 MA Crossover](strategies/bll1992-ma-crossover/README.md) | `bll1992-ma-crossover` | 1.0.0 | draft | — | [1992-brock-lakonishok-lebaron-simple-technical-trading-rules](papers/1992-brock-lakonishok-lebaron-simple-technical-trading-rules/README.md) | [bll-ma-band-signal](functions/bll-ma-band-signal/README.md) | moving-average, trend-following, vma, fma, band |
| [BLL1992 Trading Range Breakout](strategies/bll1992-trading-range-breakout/README.md) | `bll1992-trading-range-breakout` | 1.0.0 | draft | — | [1992-brock-lakonishok-lebaron-simple-technical-trading-rules](papers/1992-brock-lakonishok-lebaron-simple-technical-trading-rules/README.md) | — | breakout, trading-range, support-resistance, trend-following, band |

## Funzioni

| Nome | Slug | Versione | Stato | MC | Fonti | Dipendenze | Tag |
|---|---|---|---|---|---|---|---|
| [BLL_MA_Band_Signal](functions/bll-ma-band-signal/README.md) | `bll-ma-band-signal` | 1.0.0 | draft | — | [1992-brock-lakonishok-lebaron-simple-technical-trading-rules](papers/1992-brock-lakonishok-lebaron-simple-technical-trading-rules/README.md) | — | moving-average, band, signal, trend-following |

## Fonti

| Anno | Titolo | Autori | Tipo | Stato | Implementazioni |
|---|---|---|---|---|---|
| 1992 | [Simple Technical Trading Rules and the Stochastic Properties of Stock Returns](papers/1992-brock-lakonishok-lebaron-simple-technical-trading-rules/README.md) | William Brock, Josef Lakonishok, Blake LeBaron | paper | extracted | [BLL1992 MA Band](indicators/bll1992-ma-band/README.md), [BLL1992 MA Crossover](strategies/bll1992-ma-crossover/README.md), [BLL1992 Trading Range Breakout](strategies/bll1992-trading-range-breakout/README.md), [BLL_MA_Band_Signal](functions/bll-ma-band-signal/README.md) |

## Mappa fonte → implementazioni

### Simple Technical Trading Rules and the Stochastic Properties of Stock Returns (1992)

Id: `1992-brock-lakonishok-lebaron-simple-technical-trading-rules` — [scheda](papers/1992-brock-lakonishok-lebaron-simple-technical-trading-rules/README.md)

- indicatore: [BLL1992 MA Band](indicators/bll1992-ma-band/README.md) — Media breve, media lunga e bande (1 ± b) delle regole di media mobile di Brock, Lakonishok e LeBaron (1992), con la media breve colorata dal segnale +1 / -1 / 0.
- strategia: [BLL1992 MA Crossover](strategies/bll1992-ma-crossover/README.md) — Regole di media mobile VMA (HoldDays = 0) e FMA (HoldDays > 0) di Brock, Lakonishok e LeBaron (1992), con banda e opzione short, ordini next bar at market.
- strategia: [BLL1992 Trading Range Breakout](strategies/bll1992-trading-range-breakout/README.md) — Regola TRB di Brock, Lakonishok e LeBaron (1992), breakout del massimo o minimo delle chiusure delle ultime Length barre con banda e holding fisso, ordini next bar at market.
- funzione: [BLL_MA_Band_Signal](functions/bll-ma-band-signal/README.md) — Segnale +1 / -1 / 0 dal confronto tra media mobile breve e media lunga con banda percentuale, nucleo delle regole VMA e FMA di Brock, Lakonishok e LeBaron (1992).

## Indice per tag

Solo le voci di codice (indicatori, strategie, funzioni): i tag delle fonti non sono inclusi.

- **band** (4): [BLL1992 MA Band](indicators/bll1992-ma-band/README.md), [BLL1992 MA Crossover](strategies/bll1992-ma-crossover/README.md), [BLL1992 Trading Range Breakout](strategies/bll1992-trading-range-breakout/README.md), [BLL_MA_Band_Signal](functions/bll-ma-band-signal/README.md)
- **breakout** (1): [BLL1992 Trading Range Breakout](strategies/bll1992-trading-range-breakout/README.md)
- **fma** (1): [BLL1992 MA Crossover](strategies/bll1992-ma-crossover/README.md)
- **moving-average** (3): [BLL1992 MA Band](indicators/bll1992-ma-band/README.md), [BLL1992 MA Crossover](strategies/bll1992-ma-crossover/README.md), [BLL_MA_Band_Signal](functions/bll-ma-band-signal/README.md)
- **overlay** (1): [BLL1992 MA Band](indicators/bll1992-ma-band/README.md)
- **signal** (1): [BLL_MA_Band_Signal](functions/bll-ma-band-signal/README.md)
- **support-resistance** (1): [BLL1992 Trading Range Breakout](strategies/bll1992-trading-range-breakout/README.md)
- **trading-range** (1): [BLL1992 Trading Range Breakout](strategies/bll1992-trading-range-breakout/README.md)
- **trend-following** (4): [BLL1992 MA Band](indicators/bll1992-ma-band/README.md), [BLL1992 MA Crossover](strategies/bll1992-ma-crossover/README.md), [BLL1992 Trading Range Breakout](strategies/bll1992-trading-range-breakout/README.md), [BLL_MA_Band_Signal](functions/bll-ma-band-signal/README.md)
- **vma** (1): [BLL1992 MA Crossover](strategies/bll1992-ma-crossover/README.md)

## Voci senza fonte

_Nessuna: tutte le voci citano almeno una fonte._
