#!/usr/bin/env python3
"""Generate a handful of sample invoice PDFs under ``examples/invoices/``.

Pure standard library - no reportlab / PIL. Each PDF is a single A4 page of
Helvetica text (one ``Tj`` per line) so the content is trivially extractable by
``processOcr`` or any fulltext pipeline. A matching ``.txt`` with the expected
plain text is written next to each PDF for tests / comparisons.

Run:  python scripts/make_sample_invoices.py
"""
from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "examples" / "invoices"

# (filename stem, list of text lines)
INVOICES: list[tuple[str, list[str]]] = [
    (
        "invoice-2026-0042-acme",
        [
            "RECHNUNG / INVOICE",
            "",
            "Acme GmbH  -  Musterstrasse 1  -  10115 Berlin",
            "USt-IdNr: DE123456789",
            "",
            "Rechnungsnummer / Invoice no.: 2026-0042",
            "Rechnungsdatum / Invoice date: 2026-02-14",
            "Kundennummer / Customer no.:   K-1007",
            "",
            "Pos  Beschreibung / Description        Menge   Einzelpreis      Betrag",
            "1    Beratung / Consulting (Std.)      8       120,00 EUR    960,00 EUR",
            "2    Reisekosten / Travel              1        74,56 EUR     74,56 EUR",
            "3    Lizenz / License (Monat)          2       100,00 EUR    200,00 EUR",
            "",
            "Nettobetrag / Net:        1.234,56 EUR",
            "USt 19% / VAT 19%:          234,57 EUR",
            "Gesamtbetrag / Total:     1.469,13 EUR",
            "",
            "Zahlbar innerhalb von 14 Tagen ohne Abzug.",
            "IBAN: DE02 1203 0000 0000 2020 51   BIC: BYLADEM1001",
        ],
    ),
    (
        "invoice-2026-0043-globex",
        [
            "INVOICE",
            "",
            "Globex Corporation  -  742 Evergreen Terrace  -  Springfield",
            "VAT: GB987654321",
            "",
            "Invoice no.: 2026-0043",
            "Invoice date: 2026-03-01",
            "Purchase order: PO-55210",
            "",
            "Item  Description                       Qty     Unit price       Amount",
            "1     Cloud storage (TB / month)        5       19.00 USD     95.00 USD",
            "2     Support plan (Gold)               1      450.00 USD    450.00 USD",
            "",
            "Subtotal:      545.00 USD",
            "Tax (0%):        0.00 USD",
            "Total due:     545.00 USD",
            "",
            "Payment terms: net 30.",
        ],
    ),
    (
        "invoice-2026-0044-initech",
        [
            "RECHNUNG",
            "",
            "Initech AG  -  Bahnhofstrasse 12  -  8001 Zuerich",
            "MwSt-Nr: CHE-123.456.789",
            "",
            "Rechnungsnummer: 2026-0044",
            "Rechnungsdatum: 2026-03-18",
            "Leistungszeitraum: Februar 2026",
            "",
            "Pos  Artikel                            Menge   Preis            Summe",
            "1    Wartungspauschale                 1       800,00 CHF    800,00 CHF",
            "2    Zusatzmodul Reporting             1       450,00 CHF    450,00 CHF",
            "",
            "Netto:           1.250,00 CHF",
            "MwSt 8,1%:         101,25 CHF",
            "Rechnungsbetrag: 1.351,25 CHF",
            "",
            "Zahlbar bis 2026-04-17.",
        ],
    ),
]


def _esc(s: str) -> str:
    return s.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def _pdf(lines: list[str]) -> bytes:
    """A minimal single-page PDF: Helvetica, 11 pt, 16 pt leading, A4."""
    content_lines = ["BT", "/F1 11 Tf", "16 TL", "56 786 Td"]
    for i, ln in enumerate(lines):
        if i:
            content_lines.append("T*")
        content_lines.append(f"({_esc(ln)}) Tj")
    content_lines.append("ET")
    content = "\n".join(content_lines).encode("latin-1", "replace")

    objs: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
    ]

    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for i, body in enumerate(objs, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + body + b"\nendobj\n"
    xref_pos = len(out)
    out += b"xref\n0 %d\n" % (len(objs) + 1)
    out += b"0000000000 65535 f \n"
    for off in offsets[1:]:
        out += b"%010d 00000 n \n" % off
    out += (
        b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
        % (len(objs) + 1, xref_pos)
    )
    return bytes(out)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for stem, lines in INVOICES:
        (OUT / f"{stem}.pdf").write_bytes(_pdf(lines))
        (OUT / f"{stem}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("wrote", (OUT / f"{stem}.pdf").relative_to(OUT.parent.parent))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
