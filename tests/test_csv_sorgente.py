# SPDX-FileCopyrightText: 2026 Alberto P
# SPDX-License-Identifier: MPL-2.0
from datetime import date

import pytest

from riorganizza_spese_sanitarie.csv_sorgente import (
    _importo_a_float,
    _parse_data,
    _pulisci,
    leggi_pagamenti,
)

INTESTAZIONE = (
    "Data emissione;Data pagamento;Numero documento;Emesso da;Denominazione;"
    "Partita IVA;Tipo spesa;Importo;Spesa detraibile;Importo totale;Detraibile"
)


def riga(
    data_emissione="",
    data_pagamento="",
    num_doc="",
    emesso_da="",
    denom="",
    piva="",
    tipo_spesa="",
    importo="",
    spesa_detr="",
    importo_tot="",
    detr="",
) -> str:
    return ";".join(
        [
            data_emissione,
            data_pagamento,
            num_doc,
            emesso_da,
            denom,
            piva,
            tipo_spesa,
            importo,
            spesa_detr,
            importo_tot,
            detr,
        ]
    )


def scrivi_csv(tmp_path, righe: list[str]):
    percorso = tmp_path / "input.csv"
    percorso.write_text("\n".join([INTESTAZIONE, *righe]) + "\n", encoding="utf-8")
    return percorso


# --- _pulisci ---


def test_pulisci_rimuove_spazi_e_apici():
    assert _pulisci("  ciao  ") == "ciao"
    assert _pulisci("'SI'") == "SI"
    assert _pulisci("") == ""


# --- _importo_a_float ---


def test_importo_a_float_stringa_vuota():
    assert _importo_a_float("") == 0.0


def test_importo_a_float_formato_italiano():
    assert _importo_a_float("25,4") == 25.4
    assert _importo_a_float("'1.234,56'") == 1234.56
    assert _importo_a_float(" 10,00 ") == 10.0


def test_importo_a_float_valore_non_numerico_solleva_errore():
    with pytest.raises(ValueError):
        _importo_a_float("non-un-numero")


# --- _parse_data ---


def test_parse_data_formati_riconosciuti():
    assert _parse_data("01-02-2026") == date(2026, 2, 1)
    assert _parse_data("01/02/2026") == date(2026, 2, 1)


def test_parse_data_vuota_o_non_riconosciuta():
    assert _parse_data("") is None
    assert _parse_data("non-una-data") is None


# --- leggi_pagamenti ---


def test_leggi_pagamenti_blocco_normale(tmp_path):
    righe = [
        riga(data_pagamento="01-02-2026", emesso_da="Farmacia Rossi"),
        riga(tipo_spesa="Farmaco", importo="12,50", spesa_detr="SI"),
        riga(tipo_spesa="Farmaco", importo="3,00", spesa_detr="NO"),
    ]
    pagamenti = leggi_pagamenti(scrivi_csv(tmp_path, righe))

    assert len(pagamenti) == 1
    p = pagamenti[0]
    assert p.data_pagamento == date(2026, 2, 1)
    assert p.emesso_da == "Farmacia Rossi"
    assert p.importi_tutti == [12.50, 3.00]
    assert p.importi_detraibili == [12.50]


def test_leggi_pagamenti_fallback_senza_sottovoci(tmp_path):
    righe = [
        riga(data_pagamento="01-02-2026", emesso_da="Studio Bianchi", importo_tot="50,00", detr="SI"),
    ]
    pagamenti = leggi_pagamenti(scrivi_csv(tmp_path, righe))

    assert len(pagamenti) == 1
    p = pagamenti[0]
    assert p.importi_tutti == [50.00]
    assert p.importi_detraibili == [50.00]


def test_leggi_pagamenti_sottovoce_orfana_solleva_errore(tmp_path):
    righe = [riga(tipo_spesa="Farmaco", importo="12,50", spesa_detr="SI")]
    with pytest.raises(ValueError, match="senza una riga di testata"):
        leggi_pagamenti(scrivi_csv(tmp_path, righe))


def test_leggi_pagamenti_ignora_righe_vuote(tmp_path):
    righe = [
        riga(data_pagamento="01-02-2026", emesso_da="Farmacia Rossi"),
        riga(),  # riga completamente vuota in mezzo al blocco
        riga(tipo_spesa="Farmaco", importo="12,50", spesa_detr="SI"),
    ]
    pagamenti = leggi_pagamenti(scrivi_csv(tmp_path, righe))

    assert len(pagamenti) == 1
    assert pagamenti[0].importi_tutti == [12.50]


def test_leggi_pagamenti_importo_totale_testata_non_valido(tmp_path):
    righe = [riga(data_pagamento="01-02-2026", emesso_da="Farmacia Rossi", importo_tot="abc")]
    with pytest.raises(ValueError, match="importo totale di testata"):
        leggi_pagamenti(scrivi_csv(tmp_path, righe))


def test_leggi_pagamenti_importo_sottovoce_non_valido(tmp_path):
    righe = [
        riga(data_pagamento="01-02-2026", emesso_da="Farmacia Rossi"),
        riga(tipo_spesa="Farmaco", importo="abc", spesa_detr="SI"),
    ]
    with pytest.raises(ValueError, match="importo di sottovoce"):
        leggi_pagamenti(scrivi_csv(tmp_path, righe))
