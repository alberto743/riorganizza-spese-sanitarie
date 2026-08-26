# SPDX-FileCopyrightText: 2026 Alberto P
# SPDX-License-Identifier: MPL-2.0
from datetime import date

from riorganizza_spese_sanitarie.csv_sorgente import Pagamento, Sottovoce
from riorganizza_spese_sanitarie.formule import _numero_per_formula, _righe_output, formula_e_totale


def test_numero_per_formula_intero_senza_decimali():
    assert _numero_per_formula(12.0) == "12"


def test_numero_per_formula_decimale_senza_zeri_superflui():
    assert _numero_per_formula(15.50) == "15.5"
    assert _numero_per_formula(15.25) == "15.25"


def test_formula_e_totale_piu_addendi():
    formula, totale = formula_e_totale([12.0, 15.0, 3.0])
    assert formula == "=12+15+3"
    assert totale == 30.0


def test_formula_e_totale_lista_vuota():
    assert formula_e_totale([]) == ("=0", 0.0)


def test_righe_output():
    pagamenti = [
        Pagamento(
            data_pagamento=date(2026, 2, 1),
            emesso_da="Farmacia Rossi",
            sottovoci=[
                Sottovoce("Farmaco", 12.50, True),
                Sottovoce("Farmaco", 3.00, False),
            ],
            importo_totale_testata=99.99,  # diverso dalla somma delle sottovoci (15.50):
            # dimostra che il totale e' ricopiato dalla testata, non ricalcolato.
        ),
    ]
    righe = list(_righe_output(pagamenti))

    assert len(righe) == 1
    data_pag, emesso_da, valore_tot, formula_detr, valore_detr = righe[0]
    assert data_pag == date(2026, 2, 1)
    assert emesso_da == "Farmacia Rossi"
    assert valore_tot == 99.99
    assert formula_detr == "=12.5"
    assert valore_detr == 12.50
