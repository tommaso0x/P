{
  Nome:        {{NAME}}
  Tipo:        indicatore ({{TYPE}})
  Versione:    1.0.0
  Data:        {{DATE}}
  Fonte:       {{PAPERS}}  (aggiungere la citazione completa della fonte)
  Descrizione: {{SUMMARY}}
  Input:       Price (serie di prezzo, default Close); Length (periodo, default 20)
  Dipendenze:  {{DEPENDS_ON}}  (funzioni da importare prima di questo studio)
  Note:        scheletro generato dal template; sostituire il calcolo di esempio
               con la logica dello studio e aggiornare la scheda README.md.
}

inputs:
    Price(Close),           { serie di prezzo usata nel calcolo }
    Length(20);             { periodo di calcolo }

variables:
    AvgValue(0);            { valore calcolato da tracciare }

{ Protezione dalle barre iniziali insufficienti }
if CurrentBar > Length then begin

    { Calcolo di esempio: sostituire con la regola del paper }
    AvgValue = Average(Price, Length);

    { Plot: un Plot per ogni valore da visualizzare (Plot1..PlotN) }
    Plot1(AvgValue, "{{NAME}}");

end;
