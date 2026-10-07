# MultiCharts e PowerLanguage Editor

Come portare i sorgenti `.pl` di questa libreria dentro MultiCharts e come riportare in libreria ciò
che si esporta dall'editor. Le voci di menu sono indicate come appaiono nelle versioni recenti del
PowerLanguage Editor; se la propria versione differisce, le stesse funzioni si trovano comunque dal
menu `File`.

## Terminologia

| In questa libreria | In MultiCharts |
|---|---|
| indicatore (`indicators/`) | **Indicator**: studio che disegna plot sul grafico |
| strategia (`strategies/`) | **Signal**: studio che genera ordini; una strategia su un grafico è l'insieme dei signal applicati |
| funzione (`functions/`) | **Function**: codice riutilizzabile richiamato per nome da altri studi |

Gli studi non sono file sul disco: vivono nel database di MultiCharts e si modificano con il
**PowerLanguage Editor** (programma separato, installato insieme a MultiCharts). Per questo in
libreria si tiene il testo del codice (`.pl`) e si incolla nell'editor.

## Creare uno studio da un file `.pl`

1. Aprire il PowerLanguage Editor.
2. `File > New` e scegliere il tipo: **Indicator**, **Signal** (per le strategie) o **Function**.
3. Inserire il **nome dello studio** esattamente come nel campo `name` della scheda (es.
   `BLL1992 MA Band`). Per le funzioni il nome deve essere **identico al nome della funzione** usato
   nel codice e al nome del file `.pl` (es. `BLL_MA_Band_Signal`): MultiCharts richiama la funzione
   con il nome dello studio, e il valore di ritorno nel codice si assegna a quello stesso nome.
   Alla creazione di una funzione l'editor chiede anche il tipo di ritorno (numerico, booleano,
   stringa) e la modalità *simple* o *series*: seguire quanto indicato nella scheda della funzione.
   Se la scheda non lo specifica, per le funzioni di questa libreria il ritorno è numerico e la
   modalità è *series* quando il codice che la richiama usa valori passati della funzione
   (es. `NomeFunzione[1]`), altrimenti *simple*.
4. Cancellare l'eventuale contenuto proposto dall'editor e **incollare il testo** del file `.pl`.
   Il modo più rapido è il pulsante **Copia codice** del catalogo come pagina web (`catalog.html`:
   `python tools/render_html.py --open`, oppure su Windows la voce `1 Apri il catalogo (pagina web
   locale)` del menu di `avvia.bat`, vedi [WINDOWS.md](WINDOWS.md#il-catalogo-come-pagina-web)):
   cercare la voce, premere **Copia codice** (compare "Copiato!"), tornare nell'editor e Ctrl+V.
   In alternativa aprire il `.pl` con un editor di testo qualsiasi, selezionare tutto, copiare.
5. **Compilare** con il comando `Compile` (menu o barra degli strumenti). Gli errori compaiono nel pannello di
   output in basso con il numero di riga; correggere, ricompilare e, se la correzione è sostanziale,
   riportarla nel `.pl` della libreria (è quello la versione di riferimento).
6. Applicare lo studio a un grafico in MultiCharts (inserimento studio dal menu del grafico, voce
   `Insert Study`): gli input dichiarati nel codice compaiono nella finestra di formato dello studio
   con i default scritti nel sorgente.

### MaxBarsBack

Uno studio che guarda molte barre passate (medie a 200 periodi, massimi su 200 giorni) ha bisogno
di altrettante barre di storia prima della prima barra calcolata. Nelle **proprietà della strategia**
(`Format > Strategy Properties`) impostare *Maximum number of bars study will reference*
(MaxBarsBack) a un valore **≥ `LongLen` (o `Length`) + 1**, es. **201** per le regole con media
lunga 200; altrimenti il backtest si interrompe con un errore MaxBarsBack. Per gli **indicatori** si
può lasciare *Auto-detect* nelle proprietà dello studio. In ogni caso il grafico deve caricare
abbastanza storia (periodo del grafico più lungo di MaxBarsBack).

## Ordine di importazione: prima le funzioni

Uno studio che richiama una funzione non ancora presente **non compila**. Quindi:

1. prima tutte le funzioni elencate in `depends_on` (ricorsivamente: se una funzione dipende da
   un'altra funzione, questa viene prima);
2. poi gli indicatori;
3. poi le strategie (signal).

Il campo `depends_on` di ogni scheda e la colonna *Dipendenze* di `CATALOG.md` dicono esattamente
cosa importare prima. Quando una funzione viene modificata e ricompilata, è buona pratica
ricompilare anche gli studi che la usano.

Per la catena di esempio:

| Ordine | Tipo in MultiCharts | Nome dello studio | Sorgente |
|---|---|---|---|
| 1 | Function | `BLL_MA_Band_Signal` | [functions/bll-ma-band-signal/BLL_MA_Band_Signal.pl](../functions/bll-ma-band-signal/BLL_MA_Band_Signal.pl) |
| 2 | Indicator | `BLL1992 MA Band` | [indicators/bll1992-ma-band/BLL1992_MA_Band.pl](../indicators/bll1992-ma-band/BLL1992_MA_Band.pl) |
| 3 | Signal | `BLL1992 MA Crossover` | [strategies/bll1992-ma-crossover/BLL1992_MA_Crossover.pl](../strategies/bll1992-ma-crossover/BLL1992_MA_Crossover.pl) |
| 4 | Signal | `BLL1992 Trading Range Breakout` | [strategies/bll1992-trading-range-breakout/BLL1992_Trading_Range_Breakout.pl](../strategies/bll1992-trading-range-breakout/BLL1992_Trading_Range_Breakout.pl) |

La strategia *Trading Range Breakout* usa solo funzioni built-in (`Highest`, `Lowest`) e non ha
dipendenze in `functions/`. Le schede di ciascuna voce sono linkate dalla
[fonte BLL 1992](../papers/1992-brock-lakonishok-lebaron-simple-technical-trading-rules/README.md).

## Backtest di una strategia

1. Applicare il signal al grafico dello strumento e del timeframe desiderati (per BLL 1992: barre
   giornaliere, prezzi di chiusura).
2. Impostare le proprietà della strategia (dal menu `Format`): quantità per ordine, commissioni,
   slippage, capitale e **MaxBarsBack** ≥ `LongLen` (o `Length`) + 1 (vedi
   [MaxBarsBack](#maxbarsback)). I sorgenti di questa libreria **non** indicano la quantità negli
   ordini proprio perché la decidono queste proprietà.
3. Leggere lo **Strategy Performance Report** (menu `View`) e annotare i risultati in
   `## Test e risultati` della scheda; salvare immagini (`*.png`, `*.jpg`), export del report
   (`*.xlsx`, `*.html`) ed elenco operazioni (`*.csv`) nella sottocartella `backtests/` della voce,
   con nome `<AAAA-MM-GG>_<strumento>_<timeframe>_<descrizione>.<ext>` (vedi
   [CONVENZIONI.md §1](CONVENZIONI.md#1-contenuto-di-una-voce)).
4. Ricordare che gli ordini sono `next bar at market`: l'esecuzione avviene all'apertura della barra
   successiva al segnale, mentre i paper spesso misurano i rendimenti sulla chiusura del giorno del
   segnale. La differenza va annotata in `## Note di implementazione`.

## Esportare e importare archivi `.pla`

Il **PowerLanguage Archive** (`.pla`) è il formato con cui il PowerLanguage Editor esporta uno o
più studi, con il loro codice, per trasferirli tra installazioni.

- **Esportare**: nel PowerLanguage Editor, `File > Export`, selezionare gli studi da includere e
  salvare il file `.pla`. Conviene esportare insieme allo studio anche le funzioni da cui dipende,
  così l'archivio è autosufficiente.
- **Importare**: `File > Import`, scegliere il file `.pla` e confermare gli studi da importare;
  l'editor compila gli studi importati. Se l'archivio non contiene le funzioni richieste, importarle
  (o crearle dai `.pl`) prima.
- In libreria il `.pla` è **facoltativo**: se lo si aggiunge, va messo nella cartella della voce e
  dichiarato nel campo `archive_file` (es. `archive_file: BLL1992_MA_Band.pla`); il validatore
  controlla che il file esista. Un `.pla` che contiene più studi va comunque associato a una sola
  voce (di norma quella di livello più alto, es. la strategia).

## Perché in git si tiene il testo `.pl` e non solo il `.pla`

- Il `.pl` è **testo semplice**: `git diff` mostra esattamente cosa è cambiato tra due versioni, le
  modifiche si possono rivedere riga per riga, cercare con `grep`, commentare in una pull request e
  ricostruire con `git blame`.
- Il `.pla` è **binario** (dichiarato tale in `.gitattributes`): git lo può solo sostituire in
  blocco, non mostra differenze né permette merge; inoltre può non essere compatibile tra versioni
  diverse di MultiCharts.
- Il `.pl` si incolla in qualsiasi versione del PowerLanguage Editor e si legge anche senza
  MultiCharts; è quindi la **versione di riferimento** del codice. Il `.pla` è solo una comodità per
  reinstallare rapidamente una catena di studi già compilati.
- Regola pratica: ogni modifica si fa (o si riporta) nel `.pl`, si aggiorna la versione nella scheda
  e, se si vuole, si riesporta il `.pla`. Un `.pla` più vecchio del `.pl` è da considerare obsoleto.

## PowerLanguage.NET

MultiCharts .NET usa **PowerLanguage.NET**, cioè codice C# (o VB.NET) con un editor e un modello di
programmazione diversi da quelli descritti qui; i sorgenti `.pl` di questa libreria non si compilano
in MultiCharts .NET senza riscrittura. Le guide di questa libreria riguardano il PowerLanguage
classico. Una voce in PowerLanguage.NET è comunque ammessa; i passi:

1. creare la voce con `new_entry.py` come per una voce PowerLanguage (es.
   `python tools/new_entry.py indicator "Nome Studio" --paper <id>`);
2. rinominare il sorgente generato da `<Nome>.pl` a `<Nome>.cs` (`.gitattributes` lo tratta già
   come testo);
3. nel front matter aggiornare `source_file: <Nome>.cs` e `language: PowerLanguage.NET`;
4. sostituire il contenuto del file con la classe C# esportata dal PowerLanguage .NET Editor
   (il codice si copia dall'editor, non è un file su disco) e descrivere nella scheda eventuali
   passaggi specifici per l'importazione.

Nel catalogo la voce compare con il suffisso `(PowerLanguage.NET)` dopo il nome.

## Promemoria

- Il nome dello studio in MultiCharts = campo `name` della scheda; per le funzioni = nome della
  funzione = nome del file `.pl`.
- Prima le funzioni, poi indicatori e strategie.
- Per incollare il codice: **Copia codice** dal catalogo come pagina web (`catalog.html`, voce `1`
  del menu di `avvia.bat` su Windows o `python tools/render_html.py --open`), poi Ctrl+V nell'editor.
- Dopo ogni modifica fatta nell'editor: riportarla nel `.pl`, aggiornare `version`/`updated`/
  `## Changelog`, rigenerare il catalogo con `python tools/build_catalog.py`. `CATALOG.md` e
  `catalog.json` non si modificano a mano.
