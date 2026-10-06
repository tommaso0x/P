{
  Nome:        {{NAME}}
  Tipo:        funzione ({{TYPE}})
  Versione:    1.0.0
  Data:        {{DATE}}
  Fonte:       {{PAPERS}}  (aggiungere la citazione completa della fonte)
  Descrizione: {{SUMMARY}}
  Input:       Price (numericseries, serie su cui calcolare);
               Length (numericsimple, periodo di calcolo)
  Dipendenze:  {{DEPENDS_ON}}  (funzioni da importare prima di questa)
  Note:        in MultiCharts il nome della funzione DEVE essere identico al nome
               dello studio e al nome di questo file senza estensione .pl, e deve
               iniziare con una lettera o con _ (non con una cifra).
               Nelle proprieta' della funzione impostare il tipo di ritorno
               (es. Numeric) e Simple/Series secondo l'uso.
               Scheletro generato dal template: sostituire il calcolo di esempio;
               la riga finale assegna gia' il risultato al nome della funzione.
}

inputs:
    Price(numericseries),   { serie di prezzo su cui calcolare }
    Length(numericsimple);  { periodo di calcolo }

variables:
    Len(1);                 { periodo effettivo, mai inferiore a 1 }

{ Gestione del caso limite Length <= 1: con periodo 1 la media coincide con il prezzo }
Len = MaxList(Length, 1);

{ Valore di ritorno di default quando le barre sono insufficienti }
Value1 = 0;

{ Calcolo di esempio: sostituire con la formula del paper }
if CurrentBar > Len then
    Value1 = Average(Price, Len);

{ Assegnazione del valore di ritorno al nome della funzione (= nome del file senza .pl) }
{{SOURCE_NAME}} = Value1;
