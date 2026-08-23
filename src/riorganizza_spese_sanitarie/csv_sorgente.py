# SPDX-FileCopyrightText: 2026 Alberto P
# SPDX-License-Identifier: MPL-2.0
"""Lettura e interpretazione del CSV di origine (export Sistema TS).

Il CSV originale elenca ogni pagamento come un "blocco" di righe: una riga
"testata" (master) seguita da una o piu' righe "sottovoce". Questo modulo
legge il blocco e lo trasforma in oggetti `Pagamento`/`Sottovoce`.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

# Indici (0-based) delle colonne del CSV Sistema TS effettivamente usate.
# Layout completo del CSV originale (15 colonne), per riferimento:
#   0 Data emissione        5 Partita IVA         10 Detraibile
#   1 Data pagamento        6 Tipo spesa          11 Pagamento
#   2 Numero documento      7 Importo             12 Rimborsato
#   3 Emesso da             8 Spesa detraibile     13 Tipo spesa rimborso
#   4 Denominazione         9 Importo totale       14 Importo rimborso
COL_DATA_EMISSIONE = 0
COL_DATA_PAGAMENTO = 1
COL_EMESSO_DA = 3
COL_TIPO_SPESA = 6
COL_IMPORTO = 7
COL_SPESA_DETRAIBILE = 8
COL_IMPORTO_TOTALE = 9
COL_DETRAIBILE = 10

# Numero minimo di colonne necessario per leggere in sicurezza fino a
# COL_DETRAIBILE; righe piu' corte (colonne finali vuote troncate da
# alcuni export) vengono completate con campi vuoti.
N_COLONNE_MINIME = COL_DETRAIBILE + 1

FORMATI_DATA_RICONOSCIUTI = ("%d-%m-%Y", "%d/%m/%Y")


def _pulisci(campo: str) -> str:
    """Rimuove spazi bianchi e gli apici singoli usati dal Sistema TS per
    marcare i campi testuali (es. 'SI', 'Tracciato', '02406911202')."""
    campo = campo.strip()
    if len(campo) >= 2 and campo[0] == "'" and campo[-1] == "'":
        campo = campo[1:-1]
    return campo.strip()


def _importo_a_float(campo: str) -> float:
    """Converte un importo in formato italiano ('25,4') in float.
    Stringa vuota -> 0.0."""
    campo = _pulisci(campo)
    if not campo:
        return 0.0
    campo = campo.replace(".", "").replace(",", ".")
    return float(campo)


def _parse_data(campo: str) -> date | None:
    """Converte una data testuale (formati 'GG-MM-AAAA' o 'GG/MM/AAAA') in
    un oggetto date. Restituisce None se il campo e' vuoto o non
    riconoscibile (in tal caso la cella verra' lasciata come testo, per non
    perdere l'informazione originale)."""
    campo = _pulisci(campo)
    if not campo:
        return None
    for formato in FORMATI_DATA_RICONOSCIUTI:
        try:
            return datetime.strptime(campo, formato).date()
        except ValueError:
            continue
    return None


def _e_riga_vuota(riga: list[str]) -> bool:
    return all(_pulisci(c) == "" for c in riga)


def _e_riga_testata(riga: list[str]) -> bool:
    """Una riga di testata (nuovo pagamento) ha almeno una delle prime
    6 colonne identificative valorizzata."""
    return any(_pulisci(c) != "" for c in riga[:6])


@dataclass
class Sottovoce:
    tipo_spesa: str
    importo: float
    detraibile: bool  # True se flag == 'SI'


@dataclass
class Pagamento:
    data_pagamento: date | str  # date se riconosciuta, stringa originale altrimenti
    emesso_da: str
    sottovoci: list[Sottovoce] = field(default_factory=list)

    # Usati solo come fallback se un blocco non ha alcuna riga sottovoce
    # (testata "orfana": l'importo e il flag detraibile sono gia' nella
    # riga di testata stessa).
    importo_totale_testata: float = 0.0
    detraibile_testata: bool = False

    @property
    def importi_tutti(self) -> list[float]:
        return [sv.importo for sv in self.sottovoci]

    @property
    def importi_detraibili(self) -> list[float]:
        return [sv.importo for sv in self.sottovoci if sv.detraibile]


def leggi_pagamenti(percorso_csv: Path) -> list[Pagamento]:
    """Legge il CSV originale e restituisce l'elenco dei pagamenti, ciascuno
    con la propria lista di sottovoci."""
    with open(percorso_csv, encoding="utf-8-sig", newline="") as f:
        righe = list(csv.reader(f, delimiter=";"))

    if not righe:
        raise ValueError("Il file CSV e' vuoto.")

    _intestazione, *righe_dati = righe

    pagamenti: list[Pagamento] = []
    corrente: Pagamento | None = None

    for n_riga, riga in enumerate(righe_dati, start=2):
        if _e_riga_vuota(riga):
            continue
        if len(riga) < N_COLONNE_MINIME:
            riga = riga + [""] * (N_COLONNE_MINIME - len(riga))

        if _e_riga_testata(riga):
            testo_data = _pulisci(riga[COL_DATA_PAGAMENTO]) or _pulisci(riga[COL_DATA_EMISSIONE])
            data_riconosciuta = _parse_data(testo_data)
            corrente = Pagamento(
                data_pagamento=data_riconosciuta if data_riconosciuta is not None else testo_data,
                emesso_da=_pulisci(riga[COL_EMESSO_DA]),
                importo_totale_testata=_importo_a_float(riga[COL_IMPORTO_TOTALE]),
                detraibile_testata=_pulisci(riga[COL_DETRAIBILE]).upper() == "SI",
            )
            pagamenti.append(corrente)
            continue

        # riga sottovoce: deve appartenere a un pagamento gia' aperto
        if corrente is None:
            raise ValueError(
                f"Riga {n_riga}: sottovoce trovata senza una riga di testata "
                f"precedente. Contenuto: {riga}"
            )
        tipo_spesa = _pulisci(riga[COL_TIPO_SPESA])
        importo = _importo_a_float(riga[COL_IMPORTO])
        if tipo_spesa == "" and importo == 0.0:
            continue  # riga sottovoce completamente vuota: la ignoriamo
        corrente.sottovoci.append(
            Sottovoce(
                tipo_spesa=tipo_spesa,
                importo=importo,
                detraibile=_pulisci(riga[COL_SPESA_DETRAIBILE]).upper() == "SI",
            )
        )

    # Fallback: pagamenti senza alcuna sottovoce esplicita -> si crea una
    # sottovoce sintetica dai dati di testata, cosi' la formula di somma
    # continua a funzionare in modo uniforme per ogni riga di output.
    for p in pagamenti:
        if not p.sottovoci:
            p.sottovoci.append(
                Sottovoce(
                    tipo_spesa="(da testata, nessuna sottovoce nel file originale)",
                    importo=p.importo_totale_testata,
                    detraibile=p.detraibile_testata,
                )
            )

    return pagamenti
