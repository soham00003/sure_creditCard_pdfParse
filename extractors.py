# extractors.py - COMPLETE FIXED VERSION
import re
from typing import List, Dict, Tuple, Optional
from config import GENERIC_LABELS, BANK_LABELS, SEARCH_WINDOW_CHARS, CARD_NEGATIVE_CONTEXT
from utils import parse_amount, parse_date, last_tail

# Support both rupee encodings that appear in PDFs
AMOUNT_TOKEN = r"[₹`]?\s*[\d,]+(?:\.\d{1,2})?"

# --------------------------- helpers (text-window) ---------------------------

def _window_after_label(full_text: str, label: str, start_idx: int) -> str:
    """Return text window starting AFTER the label (handles newline cases)."""
    j = start_idx + len(label)
    return full_text[j:j + SEARCH_WINDOW_CHARS]

def _find_after_label(text: str, labels: List[str], value_pat: str, page_num: int):
    low = text.lower()
    for lbl in labels:
        lbl_low = lbl.lower()
        idx = low.find(lbl_low)
        if idx == -1:
            continue

        # primary: immediately after the label
        win = _window_after_label(text, lbl, idx)
        m = re.search(value_pat, win, flags=re.IGNORECASE)
        if m:
            return m.group(0), {"snippet": win[:180], "page": page_num}

        # secondary: also look in the next 2 "lines"
        lines = re.split(r"[\r\n]+", text[idx: idx + SEARCH_WINDOW_CHARS])
        if len(lines) >= 2:
            blk = " ".join(lines[1:3])
            m2 = re.search(value_pat, blk, flags=re.IGNORECASE)
            if m2:
                return m2.group(0), {"snippet": blk[:180], "page": page_num}

    return None, None

def _find_amount(text, labels, page):
    v, ev = _find_after_label(text, labels, AMOUNT_TOKEN, page)
    return (parse_amount(v) if v else None), ev

def _find_date(text, labels, page):
    # handle SBI: NO PAYMENT REQUIRED/NO PAYMENT DUE
    if re.search(r"\bNO PAYMENT (REQUIRED|DUE)\b", text, re.IGNORECASE):
        return "NO PAYMENT REQUIRED", {"snippet": "NO PAYMENT REQUIRED", "page": page}
    v, ev = _find_after_label(
        text, labels,
        r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|[A-Za-z]{3,}\s+\d{1,2},?\s+\d{4}|\d{4}-\d{2}-\d{2}",
        page,
    )
    return (parse_date(v) if v else None), ev

def _bad_context(snippet_lower: str) -> bool:
    return any(bad.lower() in snippet_lower for bad in CARD_NEGATIVE_CONTEXT)

# --------------------------- helpers (word-layout) ---------------------------

_MONTH = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*"
_DATE_WORD_RE = re.compile(
    rf"(?:\d{{1,2}}[/-]\d{{1,2}}[/-]\d{{2,4}}|{_MONTH}\s+\d{{1,2}},?\s+\d{{4}}|\d{{4}}-\d{{2}}-\d{{2}})",
    re.IGNORECASE,
)

def _tokens_near_label(words: List[Dict], label_tokens: List[str], max_dx: float = 9999, max_dy: float = 150) -> Optional[Tuple[float, float, float, float]]:
    """
    Find a rough bbox around the label (sequence of tokens).
    """
    if not words:
        return None

    norm = []
    for w in words:
        txt = str(w.get("text", "")).strip()
        if not txt:
            continue
        x0 = float(w.get("x0", w.get("left", 0)))
        y0 = float(w.get("y0", w.get("top", 0)))
        x1 = float(w.get("x1", x0 + float(w.get("width", 0))))
        y1 = float(w.get("y1", y0 + float(w.get("height", 0))))
        norm.append((x0, y0, x1, y1, txt.lower()))

    toks = [t.lower() for t in label_tokens if t]
    if not toks:
        return None

    for i in range(len(norm)):
        x0, y0, x1, y1, t = norm[i]
        if toks[0] not in t:
            continue
        found = [norm[i]]
        tok_idx = 1
        j = i + 1
        while j < len(norm) and tok_idx < len(toks):
            xx0, yy0, xx1, yy1, tt = norm[j]
            if abs(yy0 - y0) > max_dy:
                break
            if toks[tok_idx] in tt:
                found.append(norm[j])
                tok_idx += 1
            j += 1
        if tok_idx == len(toks):
            minx = min(a[0] for a in found)
            miny = min(a[1] for a in found)
            maxx = max(a[2] for a in found)
            maxy = max(a[3] for a in found)
            return (minx, miny, maxx, maxy)

    return None

def _date_near_bbox(words: List[Dict], bbox: Tuple[float, float, float, float], dy_down: float = 200, dx_pad: float = 100) -> Optional[str]:
    """
    Given a bbox (label area), find a date-like token cluster just below it.
    """
    if not words or not bbox:
        return None
    minx, miny, maxx, maxy = bbox
    target_minx = minx - dx_pad
    target_maxx = maxx + dx_pad
    target_miny = maxy - 5
    target_maxy = maxy + dy_down

    region = []
    for w in words:
        x0 = float(w.get("x0", w.get("left", 0)))
        y0 = float(w.get("y0", w.get("top", 0)))
        x1 = float(w.get("x1", x0 + float(w.get("width", 0))))
        y1 = float(w.get("y1", y0 + float(w.get("height", 0))))
        if (x1 >= target_minx and x0 <= target_maxx and
            y1 >= target_miny and y0 <= target_maxy):
            region.append((y0, x0, str(w.get("text",""))))

    if not region:
        return None

    region.sort()
    line = " ".join(tok for (_, _, tok) in region)
    m = _DATE_WORD_RE.search(line)
    return m.group(0) if m else None

def _find_date_word_layout(page_words: List[Dict], labels: List[str]) -> Optional[str]:
    """
    Word-layout fallback: use proximity of date tokens below the label.
    """
    if not page_words:
        return None
    
    for raw_lbl in labels:
        toks = [t for t in re.split(r"\W+", raw_lbl) if len(t) >= 3]
        bbox = _tokens_near_label(page_words, toks)
        if not bbox:
            continue
        dt = _date_near_bbox(page_words, bbox)
        if dt:
            return parse_date(dt)
    
    # Second pass: For "PAYMENT DUE DATE", try just ["payment", "due"]
    for raw_lbl in labels:
        if "payment" in raw_lbl.lower() and "due" in raw_lbl.lower():
            toks = ["payment", "due"]
            bbox = _tokens_near_label(page_words, toks, max_dy=200)
            if bbox:
                dt = _date_near_bbox(page_words, bbox, dy_down=250)
                if dt:
                    return parse_date(dt)
    
    return None

def _find_date_icici_text_only(text: str, labels: List[str], page_num: int):
    """
    ICICI-specific: Find ALL dates, pick the one closest to "PAYMENT DUE DATE" label.
    """
    low = text.lower()
    
    # Find the position of the "payment due date" label
    label_pos = -1
    for lbl in labels:
        idx = low.find(lbl.lower())
        if idx != -1:
            label_pos = idx
            break
    
    if label_pos == -1:
        return None, None
    
    # Find ALL dates in the entire text
    all_dates = []
    for match in _DATE_WORD_RE.finditer(text):
        date_str = match.group(0)
        date_pos = match.start()
        parsed = parse_date(date_str)
        if parsed:
            distance = abs(date_pos - label_pos)
            all_dates.append((distance, date_pos, parsed, date_str))
    
    if not all_dates:
        return None, None
    
    # Sort by distance from label
    all_dates.sort(key=lambda x: x[0])
    
    # Filter to dates that appear after the label within 1000 chars
    candidates = [d for d in all_dates if d[1] > label_pos and d[0] < 1000]
    
    if candidates:
        best = candidates[0]
        snippet = text[max(0, best[1]-50):best[1]+50]
        return best[2], {"snippet": snippet, "page": page_num}
    
    # Fallback: just take the closest date overall
    best = all_dates[0]
    snippet = text[max(0, best[1]-50):best[1]+50]
    return best[2], {"snippet": snippet, "page": page_num}

def _find_date_icici(text: str, page_words: List[Dict], labels: List[str], page_num: int):
    """
    ICICI-specific date finder with multiple fallback strategies.
    """
    # Strategy 1: Word layout (if word coordinates available)
    if page_words:
        date_val = _find_date_word_layout(page_words, labels)
        if date_val:
            return date_val, {"snippet": "found via word-layout proximity", "page": page_num}
    
    # Strategy 2: Aggressive text-only search
    d, ev = _find_date_icici_text_only(text, labels, page_num)
    if d:
        return d, ev
    
    # Strategy 3: Extended text window search
    low = text.lower()
    for lbl in labels:
        lbl_low = lbl.lower()
        idx = low.find(lbl_low)
        if idx == -1:
            continue
        
        win = text[idx:idx + 500]
        m = _DATE_WORD_RE.search(win)
        if m:
            parsed = parse_date(m.group(0))
            if parsed:
                return parsed, {"snippet": win[:180], "page": page_num}
    
    # Strategy 4: Search the ENTIRE page for any date (last resort)
    m = _DATE_WORD_RE.search(text)
    if m:
        parsed = parse_date(m.group(0))
        if parsed:
            return parsed, {"snippet": text[max(0, m.start()-50):m.start()+100], "page": page_num}
    
    return None, None

# --------------------------- card last digits ---------------------------

def _find_card_tail(pages, card_labels):
    """
    Search every page for a card context label, then extract last4 (or last2) near it.
    """
    best = None; best_len = 0; evidence = {}
    for p in pages:
        text = p["text"]; low = text.lower()
        for lbl in card_labels:
            idx = low.find(lbl.lower())
            if idx == -1: continue
            win = text[max(0, idx-30): idx + SEARCH_WINDOW_CHARS]
            if _bad_context(win.lower()):
                continue
            digits, n = last_tail(win)
            if digits:
                best, best_len = digits, n
                evidence = {"snippet": win[:180], "page": p["page_num"]}
                break
        if best: break

    if not best:
        for p in pages:
            for m in re.finditer(r"(?:\d{4}\s\d{4}\s\d{4}\s\d{4}|(?:\*|X){2,}\s?\d{2,4}|XXXX\s?\d{2,4})", p["text"], flags=re.IGNORECASE):
                win = p["text"][max(0, m.start()-40): m.end()+20]
                if _bad_context(win.lower()):
                    continue
                digits, n = last_tail(win)
                if digits:
                    return digits, n, {"snippet": win[:180], "page": p["page_num"]}
    return best, best_len, evidence

# --------------------------- main field extractor ---------------------------

def _extract_fields(pages, labels, use_icici_date=False):
    """
    Main extraction logic.
    """
    rec = {
        "card_last": None, "card_mask": None,
        "total_amount_due": None, "minimum_amount_due": None,
        "payment_due_date": None, "available_credit_limit": None,
        "confidence": {}, "evidence": {}
    }

    tail, n, ev = _find_card_tail(pages, labels.get("card") or GENERIC_LABELS["card"])
    if tail:
        rec["card_last"] = tail
        rec["card_mask"] = ("XXXX " + tail) if n == 4 else ("XXXX XX" + tail)
        rec["confidence"]["card_last"] = 0.95 if n == 4 else 0.85
        rec["evidence"]["card_last"] = ev or {}

    for p in pages:
        t = p["text"]; pn = p["page_num"]; words = p.get("words") or []

        if rec["total_amount_due"] is None:
            v, ev = _find_amount(t, labels.get("total") or GENERIC_LABELS["total"], pn)
            if v is not None:
                rec["total_amount_due"] = v
                rec["confidence"]["total_amount_due"] = 0.9
                rec["evidence"]["total_amount_due"] = ev or {}

        if rec["minimum_amount_due"] is None:
            v, ev = _find_amount(t, labels.get("minimum") or GENERIC_LABELS["minimum"], pn)
            if v is not None:
                rec["minimum_amount_due"] = v
                rec["confidence"]["minimum_amount_due"] = 0.9
                rec["evidence"]["minimum_amount_due"] = ev or {}

        if rec["payment_due_date"] is None:
            date_labels = labels.get("due_date") or GENERIC_LABELS["due_date"]
            
            if use_icici_date:
                d, ev = _find_date_icici(t, words, date_labels, pn)
                if d is not None:
                    rec["payment_due_date"] = d
                    rec["confidence"]["payment_due_date"] = 0.92
                    rec["evidence"]["payment_due_date"] = ev or {}
            else:
                d, ev = _find_date(t, date_labels, pn)
                if d is not None:
                    rec["payment_due_date"] = d
                    rec["confidence"]["payment_due_date"] = 0.9
                    rec["evidence"]["payment_due_date"] = ev or {}
                else:
                    d2 = _find_date_word_layout(words, date_labels)
                    if d2:
                        rec["payment_due_date"] = d2
                        rec["confidence"]["payment_due_date"] = 0.92
                        rec["evidence"]["payment_due_date"] = {"snippet": "date found via word-layout proximity", "page": pn}

        if rec["available_credit_limit"] is None:
            v, ev = _find_amount(t, labels.get("avail_limit") or GENERIC_LABELS["avail_limit"], pn)
            if v is not None:
                rec["available_credit_limit"] = v
                rec["confidence"]["available_credit_limit"] = 0.9
                rec["evidence"]["available_credit_limit"] = ev or {}

    return rec

# --------------------------- public extractors ---------------------------

def extract_generic(pages, _labels): 
    return [_extract_fields(pages, _labels, use_icici_date=False)]

def extract_idfc(pages, bank_labels): 
    return [_extract_fields(pages, bank_labels, use_icici_date=False)]

def extract_hdfc(pages, bank_labels): 
    return [_extract_fields(pages, bank_labels, use_icici_date=False)]

def extract_sbi(pages, bank_labels):  
    return [_extract_fields(pages, bank_labels, use_icici_date=False)]

def extract_axis(pages, bank_labels): 
    return [_extract_fields(pages, bank_labels, use_icici_date=False)]

def extract_icici(pages, bank_labels):
    """ICICI extractor with enhanced date detection."""
    return [_extract_fields(pages, bank_labels, use_icici_date=True)]
