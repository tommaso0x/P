{
  Nome:        BLL1992 MA Band
  Tipo:        indicatore (indicator)
  Versione:    1.0.0
  Data:        2026-10-06
  Fonte:       Brock, W., Lakonishok, J., & LeBaron, B. (1992). Simple Technical Trading
               Rules and the Stochastic Properties of Stock Returns. The Journal of
               Finance, 47(5), 1731-1764. DOI 10.1111/j.1540-6261.1992.tb04681.x
               Paper id: 1992-brock-lakonishok-lebaron-simple-technical-trading-rules
  Descrizione: traccia sul grafico dei prezzi la media breve MA(s), la media lunga MA(l)
               e le due bande MA(l)*(1+b) e MA(l)*(1-b) delle regole di media mobile
               del paper BLL (1992). La media breve e' colorata in base al segnale della
               funzione BLL_MA_Band_Signal: verde = +1 (acquisto), rosso = -1 (vendita),
               grigio = 0 (dentro la banda, neutrale).
  Input:       Price (serie di prezzo, default Close); ShortLen (s, default 1 = prezzo);
               LongLen (l, default 50); Band (b in frazione, default 0.01)
               Default = regola MA(1, 50, 0.01) del paper.
  Dipendenze:  BLL_MA_Band_Signal (functions/bll-ma-band-signal) - importare PRIMA
               di questo indicatore.
  Note:        applicare l'indicatore sul grafico dei prezzi (scala dello strumento),
               perche' i quattro plot sono espressi in unita' di prezzo.
               I plot partono dalla barra LongLen (protezione barre insufficienti).
}

inputs:
    Price(Close),             { P_t: serie di prezzo (il paper usa la chiusura giornaliera) }
    ShortLen(1),              { s: lunghezza media breve (nel paper 1, 2, 5); 1 = prezzo }
    LongLen(50),              { l: lunghezza media lunga (nel paper 50, 150, 200) }
    Band(0.01);               { b: banda in frazione (nel paper 0 oppure 0.01) }

variables:
    ShortMA(0),               { MA_t(s) }
    LongMA(0),                { MA_t(l) }
    UpperBand(0),             { MA_t(l) * (1 + b) }
    LowerBand(0),             { MA_t(l) * (1 - b) }
    SignalValue(0);           { segnale BLL: +1, -1, 0 }

{ Protezione dalle barre iniziali insufficienti per calcolare la media lunga }
if CurrentBar >= LongLen then begin

    { Media breve: con s <= 1 coincide con il prezzo, come nel paper }
    if ShortLen <= 1 then
        ShortMA = Price
    else
        ShortMA = Average(Price, ShortLen);

    { Media lunga e bande moltiplicative MA(l)(1 +/- b) }
    LongMA = Average(Price, LongLen);
    UpperBand = LongMA * (1 + Band);
    LowerBand = LongMA * (1 - Band);

    { Segnale della regola (stessa funzione usata dalle strategie) }
    SignalValue = BLL_MA_Band_Signal(Price, ShortLen, LongLen, Band);

    { Plot in unita' di prezzo }
    Plot1(ShortMA, "MA breve");
    Plot2(LongMA, "MA lunga");
    Plot3(UpperBand, "Banda sup");
    Plot4(LowerBand, "Banda inf");

    { Colore della media breve in base al segnale: verde = buy, rosso = sell, grigio = neutrale }
    if SignalValue = 1 then begin
        SetPlotColor(1, Green);
    end
    else if SignalValue = -1 then begin
        SetPlotColor(1, Red);
    end
    else begin
        SetPlotColor(1, DarkGray);
    end;

end;
