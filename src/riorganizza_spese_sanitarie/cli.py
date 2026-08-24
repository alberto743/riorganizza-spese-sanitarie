# SPDX-FileCopyrightText: 2026 Alberto P
# SPDX-License-Identifier: MPL-2.0
"""
riorganizza_spese_sanitarie.cli

Riorganizza l'export CSV delle spese sanitarie (formato "Sistema TS / 730
precompilato") in una tabella con UNA RIGA PER PAGAMENTO SANITARIO.

Dipendenze: SOLO librerie Python (stdlib + openpyxl + odfpy). Nessuna
chiamata a programmi esterni (LibreOffice/soffice non e' richiesto): sia il
file .xlsx sia il file .ods vengono scritti direttamente in Python, formule
comprese.

Struttura del CSV originale
----------------------------
Ogni pagamento occupa un "blocco" di righe:

  - una riga "testata" (master), con Data emissione, Data pagamento,
    Numero documento, Emesso da, Denominazione, Partita IVA, Importo
    totale, Detraibile, Pagamento, Rimborsato, ... valorizzati;
  - una o piu' righe "sottovoce" immediatamente successive, in cui sono
    vuote le prime 6 colonne e sono invece valorizzate Tipo spesa,
    Importo (in euro) e Spesa detraibile (SI/NO) della sottovoce.

L'importo totale del pagamento e' la somma delle sottovoci; la spesa
detraibile e' la somma delle sole sottovoci con flag detraibile = SI.

Colonne di output (solo 4, nessuna colonna di appoggio per le sottovoci)
--------------------------------------------------------------------------
  - Data pagamento               -> vero valore data (non testo), formattata
                                     GG/MM/AAAA, riconosciuta come data dal
                                     foglio di calcolo (ordinabile,
                                     filtrabile, utilizzabile in formule di
                                     altre celle)
  - Emesso da
  - Importo totale (in euro)     -> formula ad addendi letterali, es.
                                     "=12+15+3" (tutte le sottovoci)
  - Spesa detraibile              -> formula ad addendi letterali, es.
                                     "=12+3" (solo le sottovoci con flag
                                     detraibile = SI)

Colonne scartate (elenco esplicito, non implicito) perche' ridondanti,
sistematicamente vuote nel blocco utile o non rilevanti per la finalita'
dichiarativa:
  - Data emissione (quasi sempre coincidente con Data pagamento; si tiene
    solo la seconda, che e' quella fiscalmente rilevante)
  - Numero documento, Denominazione, Partita IVA (dati identificativi del
    fornitore/documento, non necessari alla tabella di sintesi richiesta)
  - Detraibile di testata (ridondante: viene ricalcolata da zero come
    somma delle sottovoci, come mostrato nell'esempio fornito dall'utente)
  - Pagamento, Rimborsato, Tipo spesa rimborso, Importo rimborso (sempre
    vuote o costanti nei file osservati)
  - Tipo spesa, Importo e Detraibile per singola sottovoce: NON vengono
    scritte in colonne separate. I relativi importi compaiono solo come
    addendi in chiaro dentro le formule di colonna C e D.

Le celle di colonna C e D non contengono un valore numerico copiato, ma una
formula (es. "=12+3") i cui addendi sono gli importi delle sottovoci
originali: il calcolo resta verificabile leggendo la formula stessa, senza
pero' fare riferimento ad altre celle del foglio.

Uso
---
    riorganizza-spese-sanitarie INPUT.csv OUTPUT.xlsx
    riorganizza-spese-sanitarie INPUT.csv OUTPUT.ods

oppure, senza installare il pacchetto:

    python3 -m riorganizza_spese_sanitarie.cli INPUT.csv OUTPUT.xlsx

Il formato di output e' determinato dall'estensione del file indicato
(.xlsx oppure .ods).
"""

import argparse
import sys
from pathlib import Path

from . import __version__
from .csv_sorgente import leggi_pagamenti
from .scrittura_ods import scrivi_ods
from .scrittura_xlsx import scrivi_xlsx

SCRITTORI = {".xlsx": scrivi_xlsx, ".ods": scrivi_ods}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input_csv", type=Path, help="CSV di origine (export Sistema TS)")
    ap.add_argument("output", type=Path, help="File di destinazione: estensione .xlsx oppure .ods")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = ap.parse_args()

    scrittore = SCRITTORI.get(args.output.suffix.lower())
    if scrittore is None:
        ap.error(f"Estensione '{args.output.suffix}' non supportata. Usa .xlsx o .ods.")

    try:
        pagamenti = leggi_pagamenti(args.input_csv)
        max_sv = max((len(p.sottovoci) for p in pagamenti), default=0)
        print(f"Letti {len(pagamenti)} pagamenti; max sottovoci per pagamento: {max_sv}", file=sys.stderr)

        scrittore(pagamenti, args.output)
        print(f"Scritto: {args.output}", file=sys.stderr)
    except (OSError, ValueError) as exc:
        print(f"Errore: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
