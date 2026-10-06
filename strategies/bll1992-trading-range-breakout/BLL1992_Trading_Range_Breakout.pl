{
  Nome:        BLL1992 Trading Range Breakout
  Tipo:        strategia (strategy)
  Versione:    1.0.0
  Data:        2026-10-06
  Fonte:       Brock, W., Lakonishok, J., & LeBaron, B. (1992). Simple Technical Trading
               Rules and the Stochastic Properties of Stock Returns. The Journal of
               Finance, 47(5), 1731-1764. DOI 10.1111/j.1540-6261.1992.tb04681.x
               Paper id: 1992-brock-lakonishok-lebaron-simple-technical-trading-rules
  Descrizione: regola TRB (trading range breakout) del paper BLL (1992).
               Resistenza = massimo delle chiusure delle Length barre precedenti
               (esclusa la corrente); supporto = minimo delle stesse barre.
               Segnale di acquisto se P_t > Resistenza * (1 + b);
               segnale di vendita se P_t < Supporto * (1 - b).
               Si entra solo da flat. Con HoldDays > 0 la posizione copre HoldDays
               rendimenti giornalieri (nel paper 10): l'ordine di uscita e' inviato
               sulla barra in cui BarsSinceEntry = HoldDays - 1 ed eseguito
               all'apertura successiva. Con HoldDays = 0 la posizione e' tenuta fino
               al segnale opposto (estensione non testata nel paper).
  Input:       Price (serie di prezzo, default Close); Length (n, default 50);
               Band (b in frazione, default 0.01); HoldDays (default 10; 0 = fino al
               segnale opposto); AllowShort (true = short sui segnali di vendita)
  Dipendenze:  nessuna (usa solo le funzioni built-in Highest e Lowest)
  Note:        tutti gli ordini sono "next bar at market": il segnale e' calcolato
               sulla chiusura della barra t e l'ordine e' eseguito all'apertura della
               barra t+1. La quantita' e' lasciata alle proprieta' della strategia.
               Il paper non considera costi di transazione: impostarli, se voluti,
               nelle proprieta' della strategia in MultiCharts.
               Highest(Price[1], Length) e Lowest(Price[1], Length) escludono la barra
               corrente: includendola il breakout sarebbe impossibile.
               MaxBarsBack: nelle proprieta' della strategia impostare "Maximum number
               of bars study will reference" >= Length + 1 (es. 201 per Length = 200),
               altrimenti il backtest si interrompe con un errore di MaxBarsBack.
}

inputs:
    Price(Close),             { P_t: serie di prezzo (il paper usa la chiusura giornaliera) }
    Length(50),               { n: barre precedenti per massimo e minimo (nel paper 50, 150, 200) }
    Band(0.01),               { b: banda in frazione (nel paper 0 oppure 0.01) }
    HoldDays(10),             { holding fisso in barre (nel paper 10); 0 = fino al segnale opposto }
    AllowShort(true);         { true = apre short sui segnali di vendita; false = resta flat }

variables:
    Resistance(0),            { Max_t(n) = max(P(t-1), ..., P(t-n)) }
    Support(0),               { Min_t(n) = min(P(t-1), ..., P(t-n)) }
    SignalValue(0);           { +1 breakout rialzista, -1 breakout ribassista, 0 nessuno }

{ Protezione dalle barre iniziali: servono Length barre precedenti piu' quella corrente }
if CurrentBar > Length then begin

    { Resistenza e supporto del paper: massimo e minimo delle chiusure degli n giorni
      precedenti, barra corrente esclusa (la serie e' spostata di una barra con Price[1]) }
    Resistance = Highest(Price[1], Length);
    Support = Lowest(Price[1], Length);

    { Segnale TRB: buy se P_t > Max_t(n)(1+b); sell se P_t < Min_t(n)(1-b); altrimenti nessuno }
    SignalValue = 0;
    if Price > Resistance * (1 + Band) then
        SignalValue = 1;
    if Price < Support * (1 - Band) then
        SignalValue = -1;

    if MarketPosition = 0 then begin

        { Da flat si entra nella direzione del breakout }
        if SignalValue = 1 then
            Buy ("LE") next bar at market;
        if (SignalValue = -1) and AllowShort then
            SellShort ("SE") next bar at market;

    end
    else begin

        if HoldDays > 0 then begin
            { Holding fisso (paper: rendimento misurato sui 10 giorni dopo il segnale):
              i segnali intermedi sono ignorati. BarsSinceEntry(0) vale 0 sulla barra di
              ingresso; l'ordine di uscita e' inviato quando vale HoldDays - 1 ed eseguito
              all'apertura successiva, cosi' la posizione copre esattamente HoldDays
              rendimenti giornalieri (open-to-open), come i 10 rendimenti del paper }
            if BarsSinceEntry(0) >= HoldDays - 1 then begin
                if MarketPosition = 1 then
                    Sell ("LX time") next bar at market;
                if MarketPosition = -1 then
                    BuyToCover ("SX time") next bar at market;
            end;
        end
        else begin
            { HoldDays = 0 (estensione): si tiene la posizione fino al segnale opposto.
              Da long, un segnale di vendita chiude il long e, se AllowShort, apre lo
              short (SellShort inverte la posizione); da short, un segnale di acquisto
              inverte in long (Buy inverte la posizione) }
            if (MarketPosition = 1) and (SignalValue = -1) then begin
                if AllowShort then
                    SellShort ("SE") next bar at market
                else
                    Sell ("LX") next bar at market;
            end;
            if (MarketPosition = -1) and (SignalValue = 1) then
                Buy ("LE") next bar at market;
        end;

    end;

end;
