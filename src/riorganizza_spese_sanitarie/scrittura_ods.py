# SPDX-FileCopyrightText: 2026 Alberto P
# SPDX-License-Identifier: MPL-2.0
"""Scrittura .ods (odfpy) — nessuna dipendenza da LibreOffice/soffice."""

from datetime import date
from pathlib import Path

from .csv_sorgente import Pagamento
from .formule import COLORE_INTESTAZIONE, INTESTAZIONI, _righe_output


def scrivi_ods(pagamenti: list[Pagamento], percorso: Path) -> None:
    from odf.number import DateStyle, Day, Month, Number, NumberStyle, Year
    from odf.number import Text as NumberText
    from odf.opendocument import OpenDocumentSpreadsheet
    from odf.style import (
        ParagraphProperties,
        Style,
        TableCellProperties,
        TableColumnProperties,
        TextProperties,
    )
    from odf.table import Table, TableCell, TableColumn, TableRow
    from odf.text import P

    doc = OpenDocumentSpreadsheet()

    # --- stili di formato numerico/data ---
    stile_data_fmt = DateStyle(name="DataGGMMAAAA")
    stile_data_fmt.addElement(Day(style="long"))
    stile_data_fmt.addElement(NumberText(text="/"))
    stile_data_fmt.addElement(Month(style="long"))
    stile_data_fmt.addElement(NumberText(text="/"))
    stile_data_fmt.addElement(Year(style="long"))
    doc.styles.addElement(stile_data_fmt)

    stile_valuta_fmt = NumberStyle(name="Valuta2Decimali")
    stile_valuta_fmt.addElement(Number(decimalplaces="2", minintegerdigits="1", grouping="true"))
    doc.styles.addElement(stile_valuta_fmt)

    # --- stili di colonna (larghezze) ---
    larghezze_cm = ("3.2cm", "11cm", "3.5cm", "3.5cm")
    stili_colonna = []
    for i, larghezza in enumerate(larghezze_cm):
        s = Style(name=f"LarColonna{i}", family="table-column")
        s.addElement(TableColumnProperties(columnwidth=larghezza))
        doc.automaticstyles.addElement(s)
        stili_colonna.append(s)

    # --- stili di cella (font, colori, allineamento, formato dati) ---
    stile_intestazione = Style(name="Intestazione", family="table-cell")
    stile_intestazione.addElement(TableCellProperties(backgroundcolor="#" + COLORE_INTESTAZIONE))
    stile_intestazione.addElement(TextProperties(fontweight="bold", color="#FFFFFF", fontfamily="Arial"))
    stile_intestazione.addElement(ParagraphProperties(textalign="center"))
    doc.automaticstyles.addElement(stile_intestazione)

    stile_testo = Style(name="Testo", family="table-cell")
    stile_testo.addElement(TextProperties(fontfamily="Arial"))
    doc.automaticstyles.addElement(stile_testo)

    stile_data_cella = Style(name="CellaData", family="table-cell", datastylename="DataGGMMAAAA")
    stile_data_cella.addElement(TextProperties(fontfamily="Arial"))
    stile_data_cella.addElement(ParagraphProperties(textalign="center"))
    doc.automaticstyles.addElement(stile_data_cella)

    stile_formula = Style(name="CellaFormula", family="table-cell", datastylename="Valuta2Decimali")
    stile_formula.addElement(TextProperties(fontweight="bold", fontfamily="Arial"))
    doc.automaticstyles.addElement(stile_formula)

    stile_totale_etichetta = Style(name="TotaleEtichetta", family="table-cell")
    stile_totale_etichetta.addElement(TextProperties(fontweight="bold", fontfamily="Arial"))
    doc.automaticstyles.addElement(stile_totale_etichetta)

    # --- foglio e colonne ---
    table = Table(name="Spese sanitarie")
    for s in stili_colonna:
        table.addElement(TableColumn(stylename=s))

    # --- riga di intestazione ---
    riga = TableRow()
    for titolo in INTESTAZIONI:
        cella = TableCell(valuetype="string", stylename=stile_intestazione)
        cella.addElement(P(text=titolo))
        riga.addElement(cella)
    table.addElement(riga)

    # --- righe dati ---
    n_righe_dati = 0
    for data_pag, emesso_da, valore_tot, formula_detr, valore_detr in _righe_output(pagamenti):
        riga = TableRow()

        if isinstance(data_pag, date):
            cella_data = TableCell(
                valuetype="date",
                datevalue=data_pag.isoformat(),
                stylename=stile_data_cella,
            )
            cella_data.addElement(P(text=data_pag.strftime("%d/%m/%Y")))
        else:
            # data non riconosciuta nel CSV originale: resta testo, per non
            # perdere l'informazione.
            cella_data = TableCell(valuetype="string", stylename=stile_testo)
            cella_data.addElement(P(text=str(data_pag)))
        riga.addElement(cella_data)

        cella_emesso = TableCell(valuetype="string", stylename=stile_testo)
        cella_emesso.addElement(P(text=emesso_da))
        riga.addElement(cella_emesso)

        cella_tot = TableCell(valuetype="float", value=valore_tot, stylename=stile_formula)
        cella_tot.addElement(P(text=f"{valore_tot:.2f}".replace(".", ",")))
        riga.addElement(cella_tot)

        cella_detr = TableCell(
            valuetype="float", value=valore_detr, formula="of:" + formula_detr, stylename=stile_formula
        )
        cella_detr.addElement(P(text=f"{valore_detr:.2f}".replace(".", ",")))
        riga.addElement(cella_detr)

        table.addElement(riga)
        n_righe_dati += 1

    # --- riga di totale generale (SUM su range di celle: qui e' corretto
    #     riferirsi ad altre celle, perche' e' un totale complessivo su
    #     piu' pagamenti, non la scomposizione di un singolo pagamento) ---
    prima_riga_dati = 2
    ultima_riga_dati = 1 + n_righe_dati
    totale_generale = round(sum(p.importo_totale_testata for p in pagamenti), 2)
    detraibile_generale = round(sum(sv.importo for p in pagamenti for sv in p.sottovoci if sv.detraibile), 2)

    riga = TableRow()
    riga.addElement(TableCell())  # colonna A vuota

    cella_etichetta = TableCell(valuetype="string", stylename=stile_totale_etichetta)
    cella_etichetta.addElement(P(text="Totale"))
    riga.addElement(cella_etichetta)

    cella_tot_gen = TableCell(
        valuetype="float",
        value=totale_generale,
        formula=f"of:=SUM([.C{prima_riga_dati}:.C{ultima_riga_dati}])",
        stylename=stile_formula,
    )
    cella_tot_gen.addElement(P(text=f"{totale_generale:.2f}".replace(".", ",")))
    riga.addElement(cella_tot_gen)

    cella_detr_gen = TableCell(
        valuetype="float",
        value=detraibile_generale,
        formula=f"of:=SUM([.D{prima_riga_dati}:.D{ultima_riga_dati}])",
        stylename=stile_formula,
    )
    cella_detr_gen.addElement(P(text=f"{detraibile_generale:.2f}".replace(".", ",")))
    riga.addElement(cella_detr_gen)

    table.addElement(riga)

    doc.spreadsheet.addElement(table)
    percorso.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(percorso))
