{
  Nome:        BLL_MA_Band_Signal
  Tipo:        funzione (function) - tipo di ritorno Numeric, storage Series
  Versione:    1.0.0
  Data:        2026-10-06
  Fonte:       Brock, W., Lakonishok, J., & LeBaron, B. (1992). Simple Technical Trading
               Rules and the Stochastic Properties of Stock Returns. The Journal of
               Finance, 47(5), 1731-1764. DOI 10.1111/j.1540-6261.1992.tb04681.x
               Paper id: 1992-brock-lakonishok-lebaron-simple-technical-trading-rules
  Descrizione: segnale di media mobile con banda del paper BLL (1992), nucleo comune
               delle regole VMA e FMA. Confronta la media breve MA(s) con la media
               lunga MA(l) allargata di una banda b:
                 +1  se MA(s) > MA(l) * (1 + b)   (segnale di acquisto)
                 -1  se MA(s) < MA(l) * (1 - b)   (segnale di vendita)
                  0  altrimenti                   (dentro la banda: neutrale)
  Input:       Price (numericseries, serie di prezzo; il paper usa la chiusura);
               ShortLen (numericsimple, lunghezza s della media breve; 1 = prezzo);
               LongLen (numericsimple, lunghezza l della media lunga);
               Band (numericsimple, banda b in frazione: 0.01 = 1 per cento)
  Dipendenze:  nessuna (usa solo la funzione built-in Average)
  Note:        In PowerLanguage Editor la funzione DEVE essere creata con il nome
               BLL_MA_Band_Signal (identico al nome di questo file senza .pl) e con
               tipo di ritorno Numeric; come Function Storage scegliere Series
               (oppure Auto-detect): cosi' gli studi chiamanti possono riferirsi ai
               valori passati con BLL_MA_Band_Signal(...)[n].
               Restituisce 0 finche' CurrentBar < LongLen (barre insufficienti).
               Il paper non prevede una banda negativa: usare Band >= 0.
}

inputs:
    Price(numericseries),     { serie di prezzo P_t (nel paper: chiusura giornaliera del DJIA) }
    ShortLen(numericsimple),  { s = lunghezza media breve (nel paper 1, 2, 5); con 1 la media e' il prezzo }
    LongLen(numericsimple),   { l = lunghezza media lunga (nel paper 50, 150, 200) }
    Band(numericsimple);      { b = banda in frazione (nel paper 0 oppure 0.01) }

variables:
    ShortMA(0),               { MA_t(s): media mobile semplice breve }
    LongMA(0),                { MA_t(l): media mobile semplice lunga }
    UpperBand(0),             { MA_t(l) * (1 + b): soglia del segnale di acquisto }
    LowerBand(0),             { MA_t(l) * (1 - b): soglia del segnale di vendita }
    SignalValue(0);           { risultato: +1, -1 oppure 0 }

{ Valore di default: nessun segnale finche' non ci sono abbastanza barre per MA(l) }
SignalValue = 0;

if CurrentBar >= LongLen then begin

    { Media breve: con s <= 1 il paper usa direttamente il prezzo (MA a 1 giorno = P_t) }
    if ShortLen <= 1 then
        ShortMA = Price
    else
        ShortMA = Average(Price, ShortLen);

    { Media lunga MA_t(l) = (1/l) * somma di P(t-i) per i = 0 .. l-1 }
    LongMA = Average(Price, LongLen);

    { Banda b applicata in modo moltiplicativo alla media lunga, come nel paper }
    UpperBand = LongMA * (1 + Band);
    LowerBand = LongMA * (1 - Band);

    { Regola BLL: buy se MA(s) > MA(l)(1+b); sell se MA(s) < MA(l)(1-b); altrimenti neutrale }
    if ShortMA > UpperBand then begin
        SignalValue = 1;
    end
    else if ShortMA < LowerBand then begin
        SignalValue = -1;
    end
    else begin
        SignalValue = 0;
    end;

end;

{ Assegnazione del valore di ritorno al nome della funzione }
BLL_MA_Band_Signal = SignalValue;
