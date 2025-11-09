# parser.py
# Orchestrator: decrypt -> extract pages -> detect issuer -> run bank extractor(s)

import io
from typing import Any
import pikepdf
from utils import decrypt_pdf_bytes, extract_pages
from config import ISSUERS, GENERIC_LABELS, BANK_LABELS
from extractors import (
    extract_idfc, extract_hdfc, extract_sbi, extract_axis, extract_icici, extract_generic
)

EXTRACTOR_MAP = {
    "IDFC": extract_idfc,
    "HDFC": extract_hdfc,
    "SBI":  extract_sbi,
    "AXIS": extract_axis,
    "ICICI": extract_icici,
}

def _detect_issuer(pages) -> tuple[str, float]:
    text_all = "\n".join(p["text"].lower() for p in pages)
    scores = {}
    for name, cfg in ISSUERS.items():
        score = 0
        for kw in cfg["keywords"]:
            if kw in text_all:
                score += 1
        scores[name] = score
    issuer = max(scores, key=scores.get)
    conf = 1.0 if scores[issuer] > 0 else 0.0
    return issuer if conf > 0 else "UNKNOWN", conf

def parse_pdf(pdf_stream_or_bytesio: io.BytesIO, password: str | None, filename: str | None = None) -> dict[str, Any]:
    # 1) decrypt in memory
    raw = pdf_stream_or_bytesio.getvalue() if hasattr(pdf_stream_or_bytesio, "getvalue") else pdf_stream_or_bytesio.read()
    try:
        stream = decrypt_pdf_bytes(raw, password)
    except ValueError:
        return {
            "success": False,
            "error_type": "password_required",
            "error": "Incorrect password or the PDF is encrypted.",
            "issuer": None,
            "issuer_confidence": 0.0,
            "records": []
        }

    # 2) extract pages (text + words with OCR fallback)
    pages = extract_pages(stream)
    if not pages:
        return {"success": False, "error": "No pages found", "error_type": "empty", "records": []}

    # 3) detect issuer
    issuer, conf = _detect_issuer(pages)

    # 4) run bank-specific extractor (or generic)
    if issuer in EXTRACTOR_MAP:
        bank_labels = BANK_LABELS.get(issuer, GENERIC_LABELS)
        records = EXTRACTOR_MAP[issuer](pages, bank_labels)
    else:
        records = extract_generic(pages, GENERIC_LABELS)

    return {
        "success": True,
        "issuer": issuer,
        "issuer_confidence": conf,
        "records": records
    }
