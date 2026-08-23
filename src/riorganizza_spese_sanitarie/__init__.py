# SPDX-FileCopyrightText: 2026 Alberto P
# SPDX-License-Identifier: MPL-2.0
"""Riorganizza l'export CSV delle spese sanitarie in una tabella per pagamento."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("riorganizza-spese-sanitarie")
except PackageNotFoundError:
    # Pacchetto non installato (es. eseguito direttamente dai sorgenti).
    __version__ = "0.0.0"
