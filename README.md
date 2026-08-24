# riorganizza-spese-sanitarie

Riorganizza l'export CSV delle spese sanitarie (formato "Sistema TS / 730
precompilato") in una tabella con **una riga per pagamento sanitario**.

Il CSV originale elenca ogni pagamento come un blocco di righe: una riga di
"testata" seguita da una o piu' righe di "sottovoce". Questo strumento
riduce ogni blocco a una singola riga, ricalcolando l'importo totale e la
spesa detraibile come formule leggibili (es. `=12+15+3`), senza copiare
valori o usare colonne di appoggio.

## Installazione

Richiede Python >= 3.10.

```
pip install .
```

Trattandosi di uno strumento a riga di comando, e' consigliabile installarlo
con [pipx](https://pipx.pypa.io/) per non "sporcare" l'ambiente Python
generale:

```
pipx install .
```

Dipendenze: solo librerie Python (`openpyxl` per `.xlsx`, `odfpy` per
`.ods`). Nessun programma esterno (LibreOffice/soffice) e' richiesto.

## Uso

```
riorganizza-spese-sanitarie INPUT.csv OUTPUT.xlsx
riorganizza-spese-sanitarie INPUT.csv OUTPUT.ods
```

Il formato di output e' determinato dall'estensione del file indicato
(`.xlsx` oppure `.ods`).

Senza installare il pacchetto:

```
python3 -m riorganizza_spese_sanitarie.cli INPUT.csv OUTPUT.xlsx
```

## Colonne di output

| Colonna | Contenuto |
|---|---|
| Data pagamento | Vero valore data (GG/MM/AAAA), non testo |
| Emesso da | Denominazione dell'emittente |
| Importo totale (in euro) | Formula ad addendi letterali, es. `=12+15+3` |
| Spesa detraibile | Formula ad addendi letterali (solo sottovoci detraibili) |

Per i dettagli completi sulla struttura del CSV di origine e sulle colonne
scartate, vedi il docstring del modulo
[`src/riorganizza_spese_sanitarie/cli.py`](src/riorganizza_spese_sanitarie/cli.py).

## Sviluppo assistito da IA

Questo progetto e' stato sviluppato con l'assistenza di uno strumento di
intelligenza artificiale.

## Licenza

Il codice sorgente (file Python) e' distribuito sotto licenza
[MPL-2.0](LICENSE). File accessori come questo README e il `.gitignore`
sono rilasciati in pubblico dominio ([CC0-1.0](LICENSES/CC0-1.0.txt));
`CLAUDE.md` non e' concesso in licenza (tutti i diritti riservati). Il
progetto e' conforme alla specifica [REUSE](https://reuse.software/); le
attribuzioni complete sono in [`REUSE.toml`](REUSE.toml) e i testi di
licenza in [`LICENSES/`](LICENSES/).
