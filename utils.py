# utils.py - COMPLETE FIXED VERSION
import os, re
from io import BytesIO
from datetime import datetime
import pdfplumber
import pikepdf
import pytesseract
from PIL import Image

# Try to point pytesseract to the Windows binary if PATH is flaky
for cand in [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
]:
    if os.path.exists(cand):
        pytesseract.pytesseract.tesseract_cmd = cand
        break

def decrypt_pdf_bytes(pdf_bytes: bytes, password: str | None) -> BytesIO:
    """Return decrypted PDF as BytesIO. If not encrypted, returns original bytes."""
    stream = BytesIO(pdf_bytes)
    try:
        if password:
            with pikepdf.open(stream, password=password) as pdf:
                out = BytesIO(); pdf.save(out); out.seek(0); return out
        else:
            with pikepdf.open(stream) as pdf:
                out = BytesIO(); pdf.save(out); out.seek(0); return out
    except pikepdf.PasswordError:
        raise ValueError("Incorrect password - please check and try again")
    except Exception as e:
        raise ValueError(f"Error reading PDF: {str(e)}")

def _ocr_page(page):
    try:
        pil = page.to_image(resolution=300).original.convert("RGB")
    except Exception:
        return "", []
    text, words = "", []
    try:
        text = pytesseract.image_to_string(pil)
    except Exception:
        pass
    try:
        data = pytesseract.image_to_data(pil, output_type=pytesseract.Output.DICT)
        for i in range(len(data["text"])):
            t = (data["text"][i] or "").strip()
            if not t: continue
            words.append({
                "left": int(data["left"][i]), "top": int(data["top"][i]),
                "width": int(data["width"][i]), "height": int(data["height"][i]),
                "text": t
            })
    except Exception:
        pass
    return text or "", words

def extract_pages(pdf_stream: BytesIO) -> list[dict]:
    """Per-page text + word boxes. OCR when no text."""
    pages = []
    with pdfplumber.open(pdf_stream) as pdf:
        for idx, page in enumerate(pdf.pages, start=1):
            try:
                text = page.extract_text() or ""
            except Exception:
                text = ""
            try:
                words = page.extract_words(use_text_flow=True)
            except Exception:
                words = []
            if not text.strip():
                text, words = _ocr_page(page)
            pages.append({"page_num": idx, "text": normalize(text), "raw_text": text, "words": words or []})
    return pages

def normalize(s: str) -> str:
    if not s: return ""
    s = s.replace("\x00", " ")
    s = re.sub(r"[^\S\r\n]+", " ", s)
    return s.strip()

# ---- parsing helpers ----
# Support multiple rupee symbol encodings: ₹ (U+20B9), ` (backtick in some PDFs)
# Support ₹ / Rs, commas, decimals, explicit zeros, and optional CR/DR suffixes
_AMOUNT_RE_GROUPS = [
    r"(?:[₹`]|Rs\.?)?\s*0+(?:\.0{1,2})?(?:\s*(?:CR|DR))?",                    # 0 / 0.00 / ₹0.00 / 0.00 CR
    r"(?:[₹`]|Rs\.?)?\s*\d{1,3}(?:,\d{2})*,\d{3}(?:\.\d{1,2})?(?:\s*(?:CR|DR))?",  # Indian: 1,23,456.78
    r"(?:[₹`]|Rs\.?)?\s*\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?(?:\s*(?:CR|DR))?",        # Western: 123,456.78
    r"(?:[₹`]|Rs\.?)?\s*\d+(?:\.\d{1,2})?(?:\s*(?:CR|DR))?",                       # Plain: 12345.67 / 12345
]


def parse_amount(s: str | None) -> float | None:
    if not s:
        return None

    for pat in _AMOUNT_RE_GROUPS:
        m = re.search(pat, s, flags=re.IGNORECASE)
        if not m:
            continue

        token = m.group(0)

        # Strip currency, spaces, commas, CR/DR, parentheses
        cleaned = token
        cleaned = re.sub(r"\b(?:CR|DR)\b", "", cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.replace("Rs.", "").replace("Rs", "").replace("₹", "").replace("`", "")
        cleaned = cleaned.replace(",", "").replace(" ", "")
        cleaned = cleaned.strip("()")  # treat (1,234.00) as 1234.00

        # If it's just zero-like, return 0.0 directly
        if re.fullmatch(r"0+(?:\.0{1,2})?", cleaned):
            return 0.0

        # Guard against absurd long integers with no commas/decimals (likely IDs)
        if "." not in cleaned and len(cleaned) > 10 and not token.strip().startswith(("₹", "Rs", "`")):
            continue

        try:
            val = float(cleaned)
        except ValueError:
            continue

        # Final sanity: ignore impossibly huge values (ID conflation)
        if val > 10_000_000_000:
            continue

        return val

    return None


# Date patterns - support various formats
_DATE_PATTERNS = [
    r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",           # 05/09/2022 or 5-9-2022
    r"\d{1,2}\s+[A-Za-z]{3,}\s+\d{2,4}",        # 5 September 2022 or 5 Sep 2022
    r"[A-Za-z]{3,}\s+\d{1,2},?\s*\d{4}",        # September 5, 2022 or Sep 5 2022
    r"\d{4}-\d{2}-\d{2}"                        # 2022-09-05 (ISO format)
]

def parse_date(s: str | None) -> str | None:
    """
    Parse various date formats and return ISO format (YYYY-MM-DD).
    Handles full month names like 'September 5, 2022'.
    """
    if not s: return None
    
    for pat in _DATE_PATTERNS:
        m = re.search(pat, s)
        if not m: continue
        
        token = m.group(0).replace(",", "").strip()
        # Try all date formats - order matters
        for fmt in [
            "%B %d %Y", "%b %d %Y", "%d %B %Y", "%d %b %Y",
            "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y",
            "%Y-%m-%d",
        ]:
            try:
                parsed = datetime.strptime(token, fmt).date()
                return parsed.isoformat()
            except ValueError:
                continue
    return None

# Card number patterns - prefer last4, else last2
LAST4_16 = r"\b\d{4}\s\d{4}\s\d{4}\s(\d{4})\b"
MASKED4 = r"(?:\*|X){2,}\s?(\d{4})"
MASKED2 = r"(?:\*|X){2,}\s?(\d{2})\b|\bXX(\d{2})\b|\b\*\*(\d{2})\b"

def last_tail(text: str) -> tuple[str, int]:
    """
    Returns (tail_digits, length). Tries 4 first, else 2.
    """
    m = re.search(LAST4_16, text)
    if m: return m.group(1), 4
    m2 = re.search(MASKED4, text, flags=re.IGNORECASE)
    if m2: return m2.group(1), 4
    m3 = re.search(MASKED2, text, flags=re.IGNORECASE)
    if m3:
        val = next(g for g in m3.groups() if g)
        return val, 2
    return None, 0
