# SPDX-FileCopyrightText: 2026 Alberto P
# SPDX-License-Identifier: MPL-2.0
"""Costruzione della formula ad addendi letterali e delle righe di output.

Su richiesta esplicita: nessuna colonna di appoggio per le sottovoci. La
colonna "Spesa detraibile" contiene una formula coi singoli importi
scritti in chiaro (es. "=12+15+3"), non un riferimento ad altre celle. La
colonna "Importo totale" riporta invece il valore gia' presente nella riga
di testata del CSV di origine (`importo_totale_testata`), senza
ricalcolarlo dalle sottovoci. Questo modulo e' condiviso dagli scrittori
xlsx e ods per evitare di duplicare la logica di calcolo.
"""

from .csv_sorgente import Pagamento

INTESTAZIONI = ["Data pagamento", "Emesso da", "Importo totale (in euro)", "Spesa detraibile"]

COLORE_INTESTAZIONE = "4472C4"
FORMATO_VALUTA = "#,##0.00"
FORMATO_DATA = "DD/MM/YYYY"


def _numero_per_formula(x: float) -> str:
    """Formatta un importo per essere inserito come addendo letterale in
    una formula (separatore decimale '.', niente zeri superflui: '12.0'
    diventa '12', '15.50' diventa '15.5')."""
    x = round(x, 2)
    if x == int(x):
        return str(int(x))
    return f"{x:.2f}".rstrip("0").rstrip(".")


def formula_e_totale(importi: list[float]) -> tuple[str, float]:
    """Costruisce la formula ad addendi letterali (es. '=12+3') e il suo
    valore numerico (calcolato qui in Python, cosi' entrambi i formati di
    output possono mostrare subito il risultato corretto anche prima di un
    eventuale ricalcolo da parte del foglio di calcolo).
    Lista vuota (nessuna sottovoce, o nessuna detraibile) -> ('=0', 0.0)."""
    totale = round(sum(importi), 2) if importi else 0.0
    if not importi:
        return "=0", totale
    return "=" + "+".join(_numero_per_formula(v) for v in importi), totale


def _righe_output(pagamenti: list[Pagamento]):
    """Genera, per ogni pagamento, la tupla di valori pronti per essere
    scritti su una riga di output: (data, emesso_da, valore_totale,
    formula_detraibile, valore_detraibile).
    Il totale e' il valore ricopiato dalla riga di testata del CSV di
    origine, non ricalcolato dalle sottovoci; la spesa detraibile resta
    invece una formula ad addendi letterali sulle sole sottovoci
    detraibili."""
    for p in pagamenti:
        formula_detr, valore_detr = formula_e_totale(p.importi_detraibili)
        yield p.data_pagamento, p.emesso_da, p.importo_totale_testata, formula_detr, valore_detr
