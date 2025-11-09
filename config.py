# config.py
# Bank keywords + rich label dictionaries + negative contexts

ISSUERS = {
    "IDFC":  {"keywords": ["idfc first", "idfc bank", "idfc first bank"]},
    "HDFC":  {"keywords": ["hdfc bank", "paytm hdfc", "hdfc credit card"]},
    "SBI":   {"keywords": ["sbi card", "simplyclick sbi", "state bank of india"]},
    "AXIS":  {"keywords": ["axis bank", "flipkart axis", "axis credit card"]},
    "ICICI": {"keywords": ["icici bank", "amazon pay icici", "icici credit card"]},
}

# We’ll look for these words around a 16-digit/masked number to accept it as "card number"
CARD_POSITIVE_LABELS = [
    "credit card number", "card number", "card no", "card #", "card no.", "primary card",
    "xxxx xxxx xxxx", "xxxx", "****", "masked",
]
# Things that look numeric but are NOT card numbers (avoid picking these)
CARD_NEGATIVE_CONTEXT = [
    "ckyc", "cKYC", "cxyc", "cif", "customer id", "customer no", "account no",
    "gstin", "gst", "ifsc", "micr", "ppn", "stmt no", "statement no", "reference no",
]

# Generic label synonyms (order from most specific to generic)
GENERIC_LABELS = {
    "total": [
        "total payment due", "total amount due", "total due", "amount due",
        "total amount payable", "amount payable", "amount to be paid",
        "total outstanding", "total balance due",
    ],
    "minimum": [
        "minimum payment due", "minimum amount due", "min amount due", "min payment due",
        "minimum due", "minimum amount payable", "min due",
    ],
    "due_date": [
        "payment due date", "due date", "last date for payment", "pay by date"
    ],
    "avail_limit": [
        "available credit (including cash)", "available credit limit (₹)", "available credit limit",
        "available limit", "avail credit limit", "available cash limit", "available credit",
    ],
    "card": CARD_POSITIVE_LABELS,
}

# Per-bank label variants (used first, then fall back to GENERIC_LABELS)
BANK_LABELS = {
    "IDFC": {
        "total": ["total amount due", "total payment due", "amount payable"],
        "minimum": ["minimum payment due", "minimum amount due", "min amount due"],
        "due_date": ["payment due date", "due date"],
        "avail_limit": ["available credit limit", "available limit", "available credit (including cash)"],
        "card": CARD_POSITIVE_LABELS,
    },
    "HDFC": {
        "total": ["total due", "total amount due", "amount payable", "total payment due"],
        "minimum": ["minimum amount due", "minimum payment due", "min payment due"],
        "due_date": ["payment due date", "due date"],
        "avail_limit": ["available credit limit", "available limit", "available credit (including cash)"],
        "card": CARD_POSITIVE_LABELS,
    },
    "SBI": {
        "total": ["*total amount due", "total outstanding", "total amount due", "total payment due"],
        "minimum": ["**minimum amount due", "minimum amount due", "minimum payment due", "min due"],
        "due_date": ["payment due date", "due date", "pay by date"],
        "avail_limit": ["available credit limit ( ₹ )", "available credit limit", "available limit", "available credit (including cash)"],
        "card": CARD_POSITIVE_LABELS,
    },
    "AXIS": {
        "total": ["total payment due", "total amount due", "total due", "amount payable"],
        "minimum": ["minimum payment due", "minimum amount due", "min amount due"],
        "due_date": ["payment due date", "due date"],
        "avail_limit": ["available credit limit", "available limit", "available credit (including cash)"],
        "card": CARD_POSITIVE_LABELS,
    },
    "ICICI": {
        "total": ["total amount due", "amount due", "total payment due", "amount payable"],
        "minimum": ["minimum amount due", "minimum payment due", "min amount"],
        "due_date": ["payment due date", "due date", "pay by date"],
        "avail_limit": ["available credit (including cash)", "available credit limit", "available limit"],
        "card": CARD_POSITIVE_LABELS,
    }
}

# regex windows / sizes
SEARCH_WINDOW_CHARS = 220
