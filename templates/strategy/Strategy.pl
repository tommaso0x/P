{
  Nome:        {{NAME}}
  Tipo:        strategia ({{TYPE}})
  Versione:    1.0.0
  Data:        {{DATE}}
  Fonte:       {{PAPERS}}  (aggiungere la citazione completa della fonte)
  Descrizione: {{SUMMARY}}
  Input:       Price (serie di prezzo, default Close); Length (periodo, default 20);
               AllowShort (true = short sui segnali di vendita, false = flat)
  Dipendenze:  {{DEPENDS_ON}}  (funzioni da importare prima di questo studio)
  Note:        scheletro generato dal template; sostituire il segnale di esempio con
               le regole del paper. Gli ordini sono sempre "next bar at market";
               la quantita' e' lasciata alle proprieta' della strategia.
}

inputs:
    Price(Close),           { serie di prezzo usata per il segnale }
    Length(20),             { periodo di calcolo }
    AllowShort(true);       { true = apre short sui segnali di vendita; false = resta flat }

variables:
    AvgValue(0),            { valore di riferimento del segnale }
    SignalValue(0);         { +1 = long, -1 = short/flat, 0 = nessun segnale }

{ Protezione dalle barre iniziali insufficienti }
if CurrentBar > Length then begin

    { Segnale di esempio: sostituire con la regola del paper }
    AvgValue = Average(Price, Length);
    SignalValue = 0;
    if Price > AvgValue then SignalValue = 1;
    if Price < AvgValue then SignalValue = -1;

    { Segnale long: chiude l'eventuale short e apre long }
    if SignalValue = 1 then begin
        if MarketPosition < 0 then
            BuyToCover ("SX") next bar at market;
        if MarketPosition <= 0 then
            Buy ("LE") next bar at market;
    end;

    { Segnale short: chiude l'eventuale long; apre short solo se AllowShort }
    if SignalValue = -1 then begin
        if MarketPosition > 0 then
            Sell ("LX") next bar at market;
        if AllowShort and (MarketPosition >= 0) then
            SellShort ("SE") next bar at market;
    end;

end;
