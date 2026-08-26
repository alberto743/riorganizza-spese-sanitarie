# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Single-file Python script (`riorganizza_spese_sanitarie.py`) that reorganizes a "Sistema TS / 730 precompilato" health-expense CSV export into a spreadsheet (`.xlsx` or `.ods`) with **one row per payment**. Everything — reading, parsing, and both spreadsheet writers — lives in this one file; there is no package structure, test suite, or build system.

## Commands

Run the script:
```
python3 riorganizza_spese_sanitarie.py INPUT.csv OUTPUT.xlsx
python3 riorganizza_spese_sanitarie.py INPUT.csv OUTPUT.ods
```
Output format is selected by the output file's extension (only `.xlsx` and `.ods` are supported).

Dependencies: stdlib + `openpyxl` (for `.xlsx`) + `odfpy` (for `.ods`). No external programs (e.g. LibreOffice/soffice) are invoked — both formats are written directly in Python, including formulas. There is no requirements.txt; install manually if missing:
```
pip install openpyxl odfpy
```

There are no automated tests in this repo.

## Architecture

The script is organized into four sequential sections (see the section comments in the file):

1. **CSV parsing** (`leggi_pagamenti`) — The source CSV has a "block" structure: each payment is one *testata* (header) row (identified by `_e_riga_testata`: any of the first 6 columns non-empty) followed by zero or more *sottovoce* (line-item) rows (first 6 columns empty, only `Tipo spesa`/`Importo`/`Spesa detraibile` populated). Column indices into the 15-column source CSV are defined as `COL_*` constants near the top of the file — consult these before changing parsing logic. Payments with no line-item rows get a synthetic fallback `Sottovoce` built from the header row's own totals (see the fallback loop at the end of `leggi_pagamenti`), so downstream formula-building code can treat every payment uniformly.

2. **Formula construction** (`formula_e_totale`, `_numero_per_formula`) — This is the core design constraint of the whole script: output column "Spesa detraibile" must contain a **literal-addend formula** (e.g. `=12+15+3`), not a copied numeric value and not a reference to helper cells/columns. There is deliberately no supporting column for individual line items — the breakdown must be recoverable by reading the formula text itself. "Importo totale" is the opposite: it is the value already present on the header (*testata*) row of the source CSV (`importo_totale_testata`), copied as a plain number, not recomputed from line items and not a formula. Both the `.xlsx` and `.ods` writers use `_righe_output` to share this computation, so total/deductible logic must stay in one place.

3. **`.xlsx` writer** (`scrivi_xlsx`, via `openpyxl`) and **3b. `.ods` writer** (`scrivi_ods`, via `odfpy`) — Two independent writers producing the same 4-column layout (`Data pagamento`, `Emesso da`, `Importo totale (in euro)`, `Spesa detraibile`). Dates are written as real date values (not text) when recognized, formatted `GG/MM/AAAA`, so they remain sortable/filterable. If a date string doesn't match `%d-%m-%Y` or `%d/%m/%Y`, it is kept as-is in a text cell rather than dropped. The `.ods` writer additionally builds explicit ODF styles (date format, currency format, header fill, fonts) since odfpy has no default styling. A whole-sheet `Totale` row at the bottom of each output **does** use a real `SUM(...)` cell-range formula (unlike the per-payment rows) — this is intentional, since it aggregates across payments rather than decomposing a single payment.

4. **CLI** (`main`) — Thin argparse wrapper; dispatches to a writer via the `SCRITTORI` dict keyed by output suffix.

## Key domain rules (do not lose these when refactoring)

- Amounts in the source CSV use Italian decimal formatting (`,` decimal separator, `.` thousands separator) and may be wrapped in single quotes (Sistema TS's text-marker convention, e.g. `'SI'`); `_pulisci` and `_importo_a_float` handle both.
- "Importo totale" = the amount already on the header (*testata*) row, copied as-is (plain number, not a formula). "Spesa detraibile" = sum of only the line items flagged `SI` (deductible), recomputed from line items as a literal-addend formula. The two columns intentionally use different sources/representations — don't unify them.
- Several source columns are intentionally dropped from the output (see the module docstring for the full, explicit list and rationale) — this is a deliberate scope decision, not an oversight, so don't reintroduce them without checking with the user first.
