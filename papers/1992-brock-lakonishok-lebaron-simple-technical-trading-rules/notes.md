# Note di estrazione estese — Brock, Lakonishok & LeBaron (1992)

Appendice alla scheda [README.md](README.md): registro di verifica delle fonti e dettagli che non
servono nella scheda principale.

## 1. Registro di verifica (2026-10-06)

Contesto: dall'ambiente usato per redigere la scheda non erano raggiungibili `doi.org`, Wiley Online
Library, JSTOR, le API di Crossref, OpenAlex e Semantic Scholar, né RePEc/IDEAS in lettura diretta.
Tutte le verifiche sono state fatte tramite ricerca web, leggendo titoli e sommari dei risultati.
Chi dispone di accesso istituzionale può ripetere il controllo aprendo direttamente
<https://doi.org/10.1111/j.1540-6261.1992.tb04681.x>.

| Elemento | Esito | Come |
|---|---|---|
| Titolo, autori, rivista, 47(5), 1731–1764, dicembre 1992 | verificato | scheda IDEAS/RePEc `bla/jfinan/v47y1992i5p1731-64`; pagina Wiley "BROCK - 1992 - The Journal of Finance"; Semantic Scholar |
| DOI `10.1111/j.1540-6261.1992.tb04681.x` | verificato | la ricerca del DOI esatto restituisce la pagina Wiley dell'articolo |
| Abstract: DJIA 1897–1986, regole MA e TRB, bootstrap, modelli nulli RW / AR(1) / GARCH-M / EGARCH, buy > sell, sell negativi, buy meno volatili | verificato | abstract riportato da RePEc e Semantic Scholar |
| Definizione VMA, banda 1%, notazione `MA(s, l, b)` es. `MA(5, 150, 0.01)` | verificato | AAII Journal, "Two Technical Analysis Rules Pass Academic Muster" |
| Coppie (1,50), (1,150), (5,150), (1,200), (2,200) | verificato | sommario di ricerca su lavori che replicano BLL |
| 10 VMA + 10 FMA + 6 TRB = 26 regole | verificato | tesi Univ. Otago (sommario); Sullivan, Timmermann & White (1999) parlano di 26 regole BLL |
| FMA: rendimento sui 10 giorni dopo la penetrazione; posizione tenuta per un numero fisso di giorni | verificato | AAII Journal; sommario di lavori successivi |
| TRB: buy se la chiusura supera il massimo degli `n` giorni precedenti, sell se scende sotto il minimo | verificato | sommario di ricerca (definizione testuale) |
| Finestre TRB 50/150/200 e holding TRB di 10 giorni | **non verificato in rete** | riportati dalla specifica di progetto e dalla lettura del paper; coerenti con le 6 regole TRB (3 finestre × 2 bande) |
| Sottoperiodi 1897–1914, 1915–1938, 1939–giu 1962, lug 1962–1986 | coerente con la letteratura secondaria, **da confermare sulla Tabella I del paper** | sommario di un lavoro che replica BLL per sottoperiodo; i confini al mese non sono stati letti su una fonte primaria |
| Numero di replicazioni del bootstrap | non verificato | omesso dalla scheda |
| Medie VMA: buy ≈ 0,042%/giorno, sell ≈ −0,025%, incondizionato ≈ 0,017% | verificato come cifre riportate da AAII | non confrontate con le tabelle originali |
| Working paper 90-22, Wisconsin Madison – Social Systems | verificato | scheda IDEAS/RePEc `att/wimass/90-22` |
| Hudson, Dempsey & Keasey (1996), JBF 20(6), 1121–1132 | verificato | scheda IDEAS/RePEc |
| Bessembinder & Chan (1998), Financial Management 27(2), 5–17 | verificato | scheda IDEAS/RePEc; CityU Scholars |
| Sullivan, Timmermann & White (1999), JoF 54(5), 1647–1691, DOI 10.1111/0022-1082.00163 | verificato | scheda IDEAS/RePEc; pagina Wiley |
| Park & Irwin (2007), J. Economic Surveys 21(4), 786–826 | verificato | scheda IDEAS/RePEc `bla/jecsur/v21y2007i4p786-826` |

## 2. Corrispondenza paper → input del codice

| Concetto nel paper | Simbolo | Input PowerLanguage | Default nel codice | Valori del paper |
|---|---|---|---|---|
| lunghezza media breve | `s` | `ShortLen` | 1 | 1, 2, 5 |
| lunghezza media lunga | `l` | `LongLen` | 50 | 50, 150, 200 |
| banda | `b` | `Band` | 0.01 | 0, 0.01 |
| holding fisso (FMA / TRB) | 10 giorni | `HoldDays` | 0 (MA Crossover = VMA), 10 (TRB) | 10 |
| finestra del breakout | `n` | `Length` | 50 | 50, 150, 200 |
| "sell" = out oppure short | — | `AllowShort` | true | non distinto nel paper |
| prezzo | `P_t` | `Price` / `Close` | Close | chiusura DJIA |

Per riprodurre le 10 regole MA del paper con `BLL1992 MA Crossover`: le 5 coppie `(ShortLen,
LongLen)` × `Band ∈ {0, 0.01}`, con `HoldDays = 0` (VMA) oppure `HoldDays = 10` (FMA). Per le 6
regole TRB con `BLL1992 Trading Range Breakout`: `Length ∈ {50, 150, 200}` × `Band ∈ {0, 0.01}`,
`HoldDays = 10`.

## 3. Differenze note tra test del paper e backtest in MultiCharts

- Il paper misura rendimenti dell'indice condizionati al segnale; una strategia MultiCharts misura
  il P&L di posizioni con ingresso `next bar at market` (apertura della barra successiva).
- Holding FMA/TRB: il paper misura 10 rendimenti close-to-close dal giorno del segnale
  (`P_t → P_{t+10}`); il codice entra all'apertura di `t+1` ed esce all'apertura di `t+1+HoldDays`
  (ordine inviato quando `BarsSinceEntry(0) = HoldDays - 1`), cioè `HoldDays` rendimenti
  open-to-open. La FMA del codice entra solo su un cambio di segnale (incrocio), come nel paper.
- Il paper non ha costi di transazione né slippage; in MultiCharts vanno impostati nelle proprietà
  della strategia se si vuole un risultato realistico.
- Il DJIA del paper è un indice di prezzo (senza dividendi) e non è direttamente negoziabile; un
  backtest su future o ETF sull'indice introduce differenze (roll, dividendi, orari).
- Il bootstrap sui modelli nulli non è replicabile in PowerLanguage: è un'analisi statistica da
  fare fuori da MultiCharts sui rendimenti esportati.
