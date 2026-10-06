---
type: paper
id: 1992-brock-lakonishok-lebaron-simple-technical-trading-rules
title: Simple Technical Trading Rules and the Stochastic Properties of Stock Returns
authors: [William Brock, Josef Lakonishok, Blake LeBaron]
year: 1992
status: extracted
tags: [technical-analysis, moving-average, trading-range-breakout, bootstrap, dow-jones]
added: 2026-10-06
journal: The Journal of Finance
volume: 47
issue: 5
pages: 1731-1764
publisher: Wiley
doi: 10.1111/j.1540-6261.1992.tb04681.x
url: https://doi.org/10.1111/j.1540-6261.1992.tb04681.x
summary: Test di regole di media mobile (VMA, FMA) e trading range breakout sul Dow Jones 1897-1986, con bootstrap contro random walk, AR(1), GARCH-M ed EGARCH.
---

# Simple Technical Trading Rules and the Stochastic Properties of Stock Returns

> **PDF non incluso.** L'articolo è protetto da copyright (Wiley / American Finance Association) e
> non viene ridistribuito in questo repository: il puntatore alla fonte è il `doi`/`url` nel front
> matter. Per averlo in locale, scaricarlo con una licenza valida (JSTOR, Wiley Online Library,
> accesso istituzionale), salvarlo in questa cartella come `paper.pdf` e aggiungere la riga
> `pdf: paper.pdf` al front matter (`build_catalog.py` verifica che il file esista). Non committare
> il PDF se non si hanno i diritti per distribuirlo; per file pesanti vedere la nota su Git LFS in
> `.gitattributes`.

## Riferimento

Brock, W., Lakonishok, J., & LeBaron, B. (1992). Simple Technical Trading Rules and the Stochastic
Properties of Stock Returns. *The Journal of Finance*, 47(5), 1731–1764.
https://doi.org/10.1111/j.1540-6261.1992.tb04681.x

Dati bibliografici (titolo, autori, rivista, volume 47, fascicolo 5, pagine 1731–1764, dicembre
1992, DOI) verificati il 2026-10-06 tramite le schede RePEc/IDEAS, Wiley Online Library e Semantic
Scholar. Esiste anche una versione working paper precedente (vedi *Riferimenti correlati*).

## Sintesi

Il paper chiede se due tra le regole di analisi tecnica più semplici e diffuse — l'incrocio di
medie mobili e il *trading range breakout* — abbiano potere predittivo sui rendimenti giornalieri
del Dow Jones Industrial Average nel periodo 1897–1986. Gli autori definiscono 26 regole (10 di
media mobile a lunghezza variabile, 10 a lunghezza fissa, 6 di breakout) e confrontano i rendimenti
nei giorni successivi ai segnali di acquisto con quelli successivi ai segnali di vendita e con il
rendimento incondizionato dell'indice.

Oltre ai test statistici tradizionali, usano il *bootstrap*: stimano quattro modelli nulli per i
rendimenti (random walk, AR(1), GARCH-M, GARCH esponenziale), simulano serie artificiali da ciascun
modello e vi applicano le stesse regole, per vedere se le proprietà stocastiche note dei rendimenti
bastano a spiegare i risultati osservati.

Risultato: i segnali di acquisto producono rendimenti sistematicamente più alti dei segnali di
vendita, i rendimenti dopo i segnali di vendita sono negativi e quelli dopo i segnali di acquisto
sono meno volatili; nessuno dei quattro modelli nulli riproduce questi fatti. Il paper non considera
costi di transazione: misura la capacità predittiva delle regole, non la loro profittabilità netta.
Il rischio di *data snooping* legato alla scelta delle regole è stato quantificato in seguito da
Sullivan, Timmermann e White (1999) sullo stesso universo di regole.

## Idee chiave

- Separare il **potere predittivo** di una regola dalla sua profittabilità: si confrontano i
  rendimenti medi condizionati al segnale (buy, sell) con il rendimento incondizionato.
- **Banda** `b` intorno alla media lunga per ridurre i falsi segnali (*whiplash*): dentro la banda
  non si opera (posizione neutra).
- Due modi di gestire la posizione dopo un segnale: **variabile** (VMA: si resta in posizione finché
  il segnale non cambia) e **fissa** (FMA: si tiene per 10 giorni e si ignorano gli altri segnali).
- **Trading range breakout** (TRB): supporto e resistenza definiti come minimo e massimo delle
  chiusure degli ultimi `n` giorni; si opera alla rottura, con la stessa banda `b`.
- **Bootstrap su modelli nulli**: per giudicare una regola non basta il t-test, perché i rendimenti
  hanno volatilità condizionata e autocorrelazione; si simulano serie da modelli che riproducono
  queste proprietà e si verifica se la regola vi funziona altrettanto bene.
- **Asimmetria buy/sell**: i rendimenti dopo i segnali di vendita sono negativi e più volatili; i
  modelli di equilibrio correnti non lo spiegano facilmente.
- Il segnale di vendita significa "fuori dal mercato o short": nel paper la distinzione non incide
  sul test, nel codice è un parametro (`AllowShort`).

## Regole / Formule

Notazione: `P_t` chiusura del giorno `t`; `MA_t(k) = (1/k) · Σ_{i=0}^{k-1} P_{t-i}` media mobile
semplice a `k` giorni; `s` lunghezza della media breve, `l` lunghezza della media lunga (`s < l`);
`b` banda percentuale (0 oppure 0,01). Il paper indica una regola di media mobile con la terna
`(s, l, b)`, per esempio `MA(5, 150, 0.01)`. Con `s = 1` la media breve coincide con il prezzo.

**VMA — Variable-Length Moving Average**

- Segnale di acquisto al giorno `t` se `MA_t(s) > MA_t(l) · (1 + b)`.
- Segnale di vendita al giorno `t` se `MA_t(s) < MA_t(l) · (1 − b)`.
- Se `MA_t(l) · (1 − b) ≤ MA_t(s) ≤ MA_t(l) · (1 + b)` non c'è segnale: posizione neutra (con
  `b = 0` accade solo in caso di uguaglianza esatta `MA_t(s) = MA_t(l)`).
- La posizione segue il segnale giorno per giorno e cambia ogni volta che il segnale cambia; con
  `b = 0` si è praticamente sempre in posizione (long oppure out/short).
- Il rendimento attribuito al segnale è quello del giorno successivo al segnale.

**FMA — Fixed-Length Moving Average**

- Stessa condizione di incrocio della VMA: il segnale nasce quando la media breve *attraversa* la
  media lunga (con banda: quando esce dalla banda verso l'alto o verso il basso).
- Dopo il segnale la posizione è tenuta per un numero **fisso** di 10 giorni di borsa e si misura il
  rendimento cumulato su quei 10 giorni; gli altri segnali che compaiono nella finestra sono
  ignorati.

**TRB — Trading Range Breakout**

- Resistenza al giorno `t`: `Max_t(n) = max(P_{t-1}, …, P_{t-n})`; supporto:
  `Min_t(n) = min(P_{t-1}, …, P_{t-n})`, cioè massimo e minimo delle chiusure degli `n` giorni
  precedenti.
- Segnale di acquisto se `P_t > Max_t(n) · (1 + b)`; segnale di vendita se
  `P_t < Min_t(n) · (1 − b)`.
- Rendimento misurato su una finestra di 10 giorni dopo il segnale, come per la FMA.

## Parametri usati nel paper

| Parametro | Valori nel paper | Note |
|-----------|------------------|------|
| `s` (media breve) | 1, 2, 5 | con `s = 1` la media breve è il prezzo di chiusura |
| `l` (media lunga) | 50, 150, 200 | |
| coppie `(s, l)` | (1, 50), (1, 150), (5, 150), (1, 200), (2, 200) | 5 coppie × 2 bande = 10 regole VMA e 10 regole FMA |
| banda `b` | 0, 0.01 | 1% sopra e sotto la media lunga; stessa banda per la TRB |
| holding FMA | 10 giorni | i segnali nella finestra sono ignorati |
| `n` (finestra TRB) | 50, 150, 200 | 3 finestre × 2 bande = 6 regole TRB |
| holding TRB | 10 giorni | come la FMA |
| prezzo | chiusura giornaliera | DJIA |
| costi di transazione | nessuno | il paper misura la predittività, non il profitto netto |
| numero totale di regole | 26 | 10 VMA + 10 FMA + 6 TRB |

## Dati e risultati del paper

- **Dati**: chiusure giornaliere del Dow Jones Industrial Average dal 1897 al 1986 (circa 90
  anni), analizzate sull'intero campione e su quattro sottoperiodi: gennaio 1897–dicembre 1914,
  gennaio 1915–dicembre 1938, gennaio 1939–giugno 1962, luglio 1962–dicembre 1986. Il DJIA è un
  indice di prezzo, quindi i rendimenti non includono i dividendi.
- **Buy vs sell**: in tutte le regole i rendimenti medi dopo i segnali di acquisto superano quelli
  dopo i segnali di vendita; i rendimenti dopo i segnali di vendita sono negativi; la volatilità dopo
  i segnali di acquisto è inferiore a quella dopo i segnali di vendita. Una sintesi divulgativa dei
  risultati (AAII Journal) riporta, come media sulle regole VMA, circa +0,042% al giorno dopo i
  segnali buy (≈12% annuo) e −0,025% dopo i segnali sell (≈−7% annuo), contro un rendimento
  incondizionato di circa 0,017% al giorno (≈4% annuo).
- **Bootstrap**: i rendimenti condizionati ai segnali non sono compatibili con i quattro modelli
  nulli considerati — random walk, AR(1), GARCH-M e GARCH esponenziale: le serie simulate da questi
  modelli non riproducono la differenza buy–sell osservata.
- **Conclusione degli autori**: forte supporto alle strategie tecniche esaminate, nel senso che i
  segnali contengono informazione sui rendimenti successivi; l'assenza di costi di transazione
  impedisce di leggere i risultati come profitti netti realizzabili.

## Note di estrazione

**Verifica delle fonti (2026-10-06).** Le pagine degli editori (Wiley, JSTOR, doi.org) e le API
bibliografiche non erano raggiungibili dall'ambiente in cui è stata redatta la scheda; la verifica è
avvenuta tramite ricerca web sui risultati di RePEc/IDEAS, Wiley Online Library, Semantic Scholar,
AAII Journal e di lavori successivi che riassumono il paper. Risultano verificati: dati
bibliografici e DOI; abstract (dati 1897–1986, regole MA e TRB, bootstrap, quattro modelli nulli,
buy > sell, sell negativi, buy meno volatili); la definizione VMA con banda dell'1% e la notazione
`MA(s, l, b)`; le cinque coppie `(s, l)`; il conteggio 10 VMA + 10 FMA + 6 TRB; la definizione TRB
come massimo/minimo delle chiusure degli `n` giorni precedenti; la logica FMA a holding fisso con
rendimento misurato sui 10 giorni successivi; i quattro sottoperiodi. **Non** è stato possibile
verificare direttamente in rete le finestre TRB 50/150/200 e l'holding di 10 giorni per la TRB (sono
riportati dalla specifica di progetto e dalla lettura del paper, e sono coerenti con le sei regole
TRB), né il numero di replicazioni del bootstrap, che per questo non è indicato. Le cifre
percentuali dei rendimenti provengono dalla sintesi AAII, non dalle tabelle originali.

**Ambiguità e decisioni prese nel codice.**

1. *Momento di ingresso.* Il paper calcola il segnale sulla chiusura del giorno `t` e attribuisce
   al segnale il rendimento del giorno `t+1` (chiusura su chiusura). In PowerLanguage gli ordini sono
   `next bar at market`: il segnale è valutato sulla barra `t` e l'ingresso avviene all'apertura della
   barra `t+1`. Il rendimento catturato è quindi open-to-close della barra successiva, non
   close-to-close; la differenza è piccola su dati giornalieri ma esiste.
2. *Segnale di vendita: flat o short.* Nel paper "sell" significa stare fuori dal mercato oppure
   short, e la scelta non cambia il test. Le strategie espongono l'input `AllowShort`: `true` apre
   posizioni short sui segnali di vendita, `false` chiude il long e resta flat.
3. *"Giorni precedenti" nella TRB.* Il massimo e il minimo sono calcolati **escludendo** la barra
   corrente: `Highest(Price[1], Length)` e `Lowest(Price[1], Length)` con `Price = Close`, cioè la
   serie spostata indietro di una barra. Includere la barra corrente renderebbe impossibile il
   breakout (`Close` non può superare un massimo che la contiene).
4. *Banda.* La banda è applicata moltiplicativamente alla media lunga (`MA(l)·(1 ± b)`) e, per la
   TRB, al massimo/minimo (`Max·(1 + b)`, `Min·(1 − b)`), come percentuale. Con `Band = 0` non esiste
   zona neutra. La funzione `BLL_MA_Band_Signal` restituisce +1 / −1 / 0 (sopra la banda superiore /
   sotto la banda inferiore / dentro la banda).
5. *VMA vs FMA nello stesso codice.* Nella strategia di incrocio l'input `HoldDays` seleziona la
   variante: `HoldDays = 0` riproduce la VMA (la posizione segue lo *stato* del segnale barra per
   barra); `HoldDays > 0` riproduce la FMA: si entra solo quando il segnale *cambia* (incrocio o
   uscita dalla banda, `SignalValue[1] <> SignalValue`), i segnali intermedi sono ignorati e allo
   scadere dell'holding si resta flat finché non si verifica un nuovo incrocio. La TRB usa
   `HoldDays = 10` di default ed entra sul breakout da flat.
   *Durata dell'holding.* Il paper misura 10 rendimenti close-to-close dal giorno del segnale
   (`P_t → P_{t+10}`). Nel codice l'ingresso avviene all'apertura di `t+1` e l'ordine di uscita è
   inviato quando `BarsSinceEntry(0) = HoldDays - 1`, eseguito all'apertura di `t+1+HoldDays`: la
   posizione copre esattamente `HoldDays` rendimenti giornalieri (open-to-open). Con la condizione
   `>= HoldDays` la posizione sarebbe durata un giorno di più.
6. *Media breve con `s = 1`.* `Average(Close, 1)` coincide con il prezzo: il codice gestisce il
   caso esplicitamente per evitare dipendenze dal comportamento della funzione built-in.
7. *Costi di transazione e slippage.* Non sono nel paper e non sono nel codice: per un backtest
   realistico vanno impostati nelle proprietà della strategia in MultiCharts.
8. *Barre insufficienti.* Il paper scarta semplicemente il periodo iniziale necessario a calcolare
   la media lunga; il codice protegge i calcoli con `CurrentBar >= LongLen` (funzione, indicatore,
   MA Crossover) e `CurrentBar > Length` (TRB, che richiede le `Length` barre precedenti più la
   corrente). Nelle strategie va inoltre impostato MaxBarsBack ≥ `LongLen + 1` (o `Length + 1`)
   nelle proprietà della strategia.
9. *Sottoperiodi e bootstrap.* Non sono replicati nel codice: il bootstrap sui modelli nulli è un
   test statistico fuori dall'ambito di uno studio PowerLanguage. I sottoperiodi si ottengono
   limitando l'intervallo dati nel backtest.

Note estese: registro di verifica delle fonti e tabella paper → input del codice in
[notes.md](notes.md).

## Implementazioni in questa libreria

- [BLL_MA_Band_Signal](../../functions/bll-ma-band-signal/README.md) — funzione: segnale
  +1 / −1 / 0 dal confronto tra media breve e media lunga con banda `b` (nucleo di VMA e FMA).
- [BLL1992 MA Band](../../indicators/bll1992-ma-band/README.md) — indicatore: media breve, media
  lunga e bande `(1 ± b)` sul grafico, con il segnale.
- [BLL1992 MA Crossover](../../strategies/bll1992-ma-crossover/README.md) — strategia: regole VMA
  (`HoldDays = 0`) e FMA (`HoldDays > 0`), input `ShortLen`, `LongLen`, `Band`, `HoldDays`,
  `AllowShort`.
- [BLL1992 Trading Range Breakout](../../strategies/bll1992-trading-range-breakout/README.md) —
  strategia: regola TRB su massimo/minimo delle chiusure degli ultimi `Length` giorni con banda e
  holding fisso.

Il catalogo (`CATALOG.md`) ricava la stessa mappa dal campo `papers:` delle voci di codice.

## Riferimenti correlati

- Brock, W., Lakonishok, J., & LeBaron, B. *Simple Technical Trading Rules and the Stochastic
  Properties of Stock Returns*. Working paper n. 90-22, Wisconsin Madison – Social Systems
  (versione preliminare dell'articolo). https://ideas.repec.org/p/att/wimass/90-22.html
- Hudson, R., Dempsey, M., & Keasey, K. (1996). A note on the weak form efficiency of capital
  markets: The application of simple technical trading rules to UK stock prices – 1935 to 1994.
  *Journal of Banking & Finance*, 20(6), 1121–1132. Replica delle regole BLL sul mercato britannico.
- Bessembinder, H., & Chan, K. (1998). Market Efficiency and the Returns to Technical Analysis.
  *Financial Management*, 27(2), 5–17. Conferma i risultati BLL ma li riconduce in parte a errori di
  misura da *nonsynchronous trading* e li ritiene compatibili con l'efficienza dei mercati una volta
  considerati i costi di transazione.
- Sullivan, R., Timmermann, A., & White, H. (1999). Data-Snooping, Technical Trading Rule
  Performance, and the Bootstrap. *The Journal of Finance*, 54(5), 1647–1691.
  https://doi.org/10.1111/0022-1082.00163 — applica il *Reality Check* di White alle 26 regole BLL e
  a un universo molto più ampio su 100 anni di DJIA, quantificando il *data snooping*.
- Park, C.-H., & Irwin, S. H. (2007). What Do We Know About the Profitability of Technical
  Analysis? *Journal of Economic Surveys*, 21(4), 786–826.
  https://doi.org/10.1111/j.1467-6419.2007.00519.x — rassegna della letteratura successiva.
