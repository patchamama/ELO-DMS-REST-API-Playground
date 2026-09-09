"""The committed sample invoices must match what the generator produces."""
import importlib.util
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
_GEN = _ROOT / "scripts" / "make_sample_invoices.py"
_OUT = _ROOT / "examples" / "invoices"


def _load():
    spec = importlib.util.spec_from_file_location("make_sample_invoices", _GEN)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["make_sample_invoices"] = mod
    spec.loader.exec_module(mod)
    return mod


gen = _load()


def test_sample_invoice_pdfs_are_committed_and_in_sync():
    assert _OUT.is_dir(), "run: python scripts/make_sample_invoices.py"
    for stem, lines in gen.INVOICES:
        pdf = _OUT / f"{stem}.pdf"
        txt = _OUT / f"{stem}.txt"
        assert pdf.is_file() and txt.is_file(), f"missing {stem}"
        assert pdf.read_bytes() == gen._pdf(lines), f"{stem}.pdf out of sync - re-run the generator"
        assert txt.read_text(encoding="utf-8") == "\n".join(lines) + "\n"
        assert pdf.read_bytes().startswith(b"%PDF-1.")
        assert pdf.read_bytes().rstrip().endswith(b"%%EOF")


def test_generator_lines_carry_extractable_fields():
    joined = "\n".join(l for _, ls in gen.INVOICES for l in ls)
    assert "2026-0042" in joined and "1.469,13 EUR" in joined
