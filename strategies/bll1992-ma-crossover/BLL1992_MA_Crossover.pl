{
  Nome:        BLL1992 MA Crossover
  Tipo:        strategia (strategy)
  Versione:    1.0.0
  Data:        2026-10-06
  Fonte:       Brock, W., Lakonishok, J., & LeBaron, B. (1992). Simple Technical Trading
               Rules and the Stochastic Properties of Stock Returns. The Journal of
               Finance, 47(5), 1731-1764. DOI 10.1111/j.1540-6261.1992.tb04681.x
               Paper id: 1992-brock-lakonishok-lebaron-simple-technical-trading-rules
  Descrizione: regole di media mobile del paper BLL (1992) in un'unica strategia.
               Il segnale e' quello della funzione BLL_MA_Band_Signal (+1 / -1 / 0).
               HoldDays = 0  -> VMA (variable-length moving average): la posizione segue
                                lo stato del segnale barra per barra; dentro la banda
                                (segnale 0) si resta flat.
               HoldDays > 0  -> FMA (fixed-length moving average): si entra solo da flat
                                e solo quando il segnale CAMBIA (incrocio / uscita dalla
                                banda); la posizione copre HoldDays rendimenti giornalieri
                                (nel paper 10) e i segnali intermedi sono ignorati.
  Input:       Price (serie di prezzo, default Close); ShortLen (s, default 1);
               LongLen (l, default 50); Band (b in frazione, default 0.01);
               HoldDays (0 = VMA; >0 = FMA con holding fisso, nel paper 10);
               AllowShort (true = short sui segnali di vendita; false = flat)
  Dipendenze:  BLL_MA_Band_Signal (functions/bll-ma-band-signal) - importare PRIMA
               di questa strategia.
  Note:        tutti gli ordini sono "next bar at market": il segnale e' calcolato
               sulla chiusura della barra t e l'ordine e' eseguito all'apertura della
               barra t+1. La quantita' e' lasciata alle proprieta' della strategia.
               Il paper non considera costi di transazione: impostarli, se voluti,
               nelle proprieta' della strategia in MultiCharts.
               Un Buy con posizione short (e un SellShort con posizione long) inverte
               la posizione in un solo ordine, come da comportamento standard di
               MultiCharts.
               MaxBarsBack: nelle proprieta' della strategia impostare "Maximum number
               of bars study will reference" >= LongLen + 1 (es. 201 per LongLen = 200),
               altrimenti il backtest si interrompe con un errore di MaxBarsBack.
}

inputs:
    Price(Close),             { P_t: serie di prezzo (il paper usa la chiusura giornaliera) }
    ShortLen(1),              { s: lunghezza media breve (nel paper 1, 2, 5); 1 = prezzo }
    LongLen(50),              { l: lunghezza media lunga (nel paper 50, 150, 200) }
    Band(0.01),               { b: banda in frazione (nel paper 0 oppure 0.01) }
    HoldDays(0),              { 0 = VMA; > 0 = FMA con holding fisso di HoldDays barre (paper: 10) }
    AllowShort(true);         { true = apre short sui segnali di vendita; false = resta flat }

variables:
    SignalValue(0);           { segnale BLL: +1 buy, -1 sell, 0 neutrale }

{ Protezione dalle barre iniziali insufficienti per calcolare la media lunga }
if CurrentBar >= LongLen then begin

    { Segnale del paper: +1 se MA(s) > MA(l)(1+b); -1 se MA(s) < MA(l)(1-b); 0 dentro la banda }
    SignalValue = BLL_MA_Band_Signal(Price, ShortLen, LongLen, Band);

    if HoldDays = 0 then begin

        { ================================================================
          VMA - Variable-Length Moving Average (parafrasi delle regole MA
          del paper): la posizione cambia ogni volta che il segnale cambia,
          cioe' replica lo stato del segnale a ogni barra.
          ================================================================ }

        if SignalValue = 1 then begin
            { Segnale di acquisto: si e' long. Se si e' flat o short si compra
              (da short il Buy inverte la posizione) }
            if MarketPosition <> 1 then
                Buy ("LE") next bar at market;
        end
        else if SignalValue = -1 then begin
            { Segnale di vendita: nel paper "sell" = fuori dal mercato oppure short }
            if AllowShort then begin
                { AllowShort = true: si e' short. Da flat o long si vende short
                  (da long il SellShort inverte la posizione) }
                if MarketPosition <> -1 then
                    SellShort ("SE") next bar at market;
            end
            else begin
                { AllowShort = false: si chiude il long e si resta flat }
                if MarketPosition = 1 then
                    Sell ("LX") next bar at market;
            end;
        end
        else begin
            { Segnale 0: MA(s) dentro la banda MA(l)(1 +/- b), posizione neutra:
              si chiude qualunque posizione aperta }
            if MarketPosition = 1 then
                Sell ("LX") next bar at market;
            if MarketPosition = -1 then
                BuyToCover ("SX") next bar at market;
        end;

    end
    else begin

        { ================================================================
          FMA - Fixed-Length Moving Average (parafrasi delle regole MA del
          paper): il segnale nasce quando la media breve attraversa la media
          lunga (con banda: quando esce dalla banda); dopo il segnale la
          posizione e' tenuta per 10 giorni fissi e gli altri segnali in
          quella finestra sono ignorati.
          ================================================================ }

        if MarketPosition = 0 then begin
            { Da flat si entra solo quando il segnale CAMBIA (incrocio), non per il
              solo fatto che MA(s) sia fuori dalla banda: SignalValue[1] e' il valore
              della variabile alla barra precedente }
            if (SignalValue = 1) and (SignalValue[1] <> 1) then
                Buy ("LE") next bar at market;
            if (SignalValue = -1) and (SignalValue[1] <> -1) and AllowShort then
                SellShort ("SE") next bar at market;
        end
        else begin
            { In posizione: i segnali sono ignorati; si esce solo allo scadere
              dell'holding fisso. BarsSinceEntry(0) vale 0 sulla barra di ingresso;
              l'ordine di uscita e' inviato quando vale HoldDays - 1 ed eseguito
              all'apertura successiva, cosi' la posizione copre esattamente HoldDays
              rendimenti giornalieri (open-to-open), come i 10 rendimenti del paper }
            if BarsSinceEntry(0) >= HoldDays - 1 then begin
                if MarketPosition = 1 then
                    Sell ("LX time") next bar at market;
                if MarketPosition = -1 then
                    BuyToCover ("SX time") next bar at market;
            end;
        end;

    end;

end;
