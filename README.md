# 💳 Credit Card Statement Parser

A Python-based PDF parser that extracts key information from credit card statements across multiple issuers.

## 🎯 Features

- **5 Supported Issuers**: HDFC, ICICI, SBI, Axis Bank, IDFC First Bank
- **5 Key Fields Extracted**:
  - Card Last 4 Digits
  - Statement Start Date
  - Statement End Date
  - Payment Due Date
  - Total Amount Due
- **Confidence Scoring**: Each extracted field comes with a confidence score
- **Web Interface**: Easy-to-use Streamlit interface
- **CSV Export**: Download extracted data

## 📁 Project Structure

```
credit-card-parser/
├── app.py                 # Streamlit web interface
├── parser.py              # PDF parsing logic
├── extractors.py          # Field extraction engine
├── config.py              # Issuer-specific dictionaries
├── utils.py              # Helper functions
├── requirements.txt       # Dependencies
├── sample_statements/    # Test PDFs
└── README.md             # This file
```

## 🚀 Installation & Setup

### 1. Prerequisites
- Python 3.10 or higher
- pip (Python package manager)

### 2. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### 3. Run the Application

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

## 📖 Usage

1. Open the web interface
2. Upload a credit card statement PDF
3. Click "Extract Information"
4. Review the extracted fields with confidence scores
5. Download results as CSV if needed

## 🔧 How It Works

### Enhanced Architecture (v2.0)

1. **PDF Parsing** (`parser.py`): 
   - Extracts text from PDFs using pdfplumber
   - **NEW**: Enhanced password handling (empty password attempt, hidden encryption detection)
   - **NEW**: Unified word bounding box extraction

2. **Issuer Detection** (`parser.py`): 
   - Identifies the card issuer using keyword matching
   - **NEW**: Gap-based confidence scoring for better reliability

3. **Field Extraction** (`extractors.py`): 
   - Uses label-based pattern matching with scoring
   - **NEW**: Euclidean distance-based nearest-neighbor value extraction
   - **NEW**: Global date range fallback when labels unclear

4. **Normalization** (`utils.py`): 
   - Handles dates, amounts, and text cleaning
   - **NEW**: Word box normalization (pdfplumber + OCR compatibility)
   - **NEW**: All-dates extraction for fallback

5. **Validation** (`validators.py`): 
   - Comprehensive data validation
   - **NEW**: Distance-based scoring confidence

6. **UI** (`app.py`): Streamlit interface for user interaction

### Extraction Strategy (Enhanced)

For each field:
1. Search for positive labels (e.g., "payment due date")
2. Exclude negative labels (e.g., "minimum")
3. **NEW**: Use Euclidean distance to find nearest value word (geometry-based)
4. Fallback to line-based extraction if word boxes unavailable
5. **NEW**: Global date range extraction as last resort
6. Score candidates based on:
   - Label match quality (exact vs fuzzy)
   - Geometric distance (NEW - replaces simple right/below)
   - Page priority (page 1 preferred)
   - Value validity
7. Select highest-scoring candidate

### Confidence Thresholds

- **≥ 75%**: High confidence (green) - reliable
- **50-75%**: Medium confidence (yellow) - review recommended
- **< 50%**: Low confidence (red) - manual verification needed

## 🧪 Testing

Place test PDFs in `sample_statements/` folder and test extraction accuracy.

## 🛠️ Customization

### Adding New Issuers

Edit `config.py` and add issuer configuration:

```python
'NEW_BANK': {
    'keywords': ['new bank', 'newbank'],
    'fields': {
        'card_last4': {
            'positive': ['card number', 'card ending'],
            'negative': []
        },
        # ... other fields
    }
}
```

### Example: IDFC First Bank Configuration

```python
'IDFC': {
    'keywords': ['idfc', 'idfc first', 'idfc first bank', 'first bank'],
    'fields': {
        'card_last4': {
            'positive': ['card number', 'card no.', 'credit card number'],
            'negative': []
        },
        'payment_due_date': {
            'positive': ['payment due date', 'due date', 'pay by date'],
            'negative': ['minimum', 'statement']
        },
        'total_amount_due': {
            'positive': ['total amount due', 'total outstanding', 'amount payable'],
            'negative': ['minimum', 'minimum amount']
        }
    }
}
```

### Adjusting Confidence Scoring

Modify weights in `extractors.py` > `_select_best_candidate()` method.

## 📊 Output Format

```json
{
  "card_last4": {
    "value": "1234",
    "confidence": 0.85,
    "page": 1,
    "source": "same_line"
  },
  "statement_start_date": {
    "value": "2024-01-01",
    "confidence": 0.90,
    "page": 1,
    "source": "next_line"
  },
  // ... other fields
}
```

## 🛡️ Security & Edge Cases

### Security Features

1. **Password Protection**
   - ✅ Handles password-protected PDFs
   - ✅ Password input via secure text field (masked)
   - ✅ Password NEVER stored or logged
   - ✅ Password cleared from memory immediately after use

2. **Data Privacy**
   - ✅ PDFs processed in temporary memory only
   - ✅ Temporary files deleted immediately after processing
   - ✅ No persistence to disk or database
   - ✅ No logging of sensitive information
   - ✅ No external API calls

3. **File Handling**
   - ✅ File size limit (50MB)
   - ✅ Automatic cleanup on errors
   - ✅ Safe file operations with error handling

### Edge Cases Handled

1. **PDF Issues**
   - ✅ **Password-protected PDFs**: Prompts user for password
   - ✅ **Corrupted PDFs**: Detects and shows friendly error
   - ✅ **Empty PDFs**: Validates page count
   - ✅ **Image-based PDFs**: Detects lack of text, suggests OCR
   - ✅ **Invalid formats**: Validates PDF structure
   - ✅ **Large files**: Handles up to 50MB with size warnings

2. **Text Extraction Issues**
   - ✅ **No extractable text**: Identifies scanned documents
   - ✅ **Partial text extraction**: Processes available pages
   - ✅ **Unicode characters**: NFKC normalization
   - ✅ **Special characters**: Handles ₹, INR, currency symbols
   - ✅ **Multi-page extraction errors**: Continues on page failures

3. **Data Quality Issues**
   - ✅ **Missing fields**: Shows "Not Found" with low confidence
   - ✅ **Ambiguous values**: Scores multiple candidates
   - ✅ **Conflicting dates**: Validates date logic
   - ✅ **Unusual amounts**: Warns on extreme values
   - ✅ **Invalid card numbers**: Validates 4-digit format

4. **Statement Variations**
   - ✅ **Zero balance statements**: Detects "No payment required"
   - ✅ **Credit balance**: Handles negative amounts
   - ✅ **Multiple currencies**: Normalizes to INR
   - ✅ **Date format variations**: Parses 6+ date formats
   - ✅ **Unknown issuers**: Falls back to generic patterns

5. **Validation Checks**
   - ✅ **Date range validation**: Start ≤ End < Due
   - ✅ **Billing cycle length**: Warns on unusual cycles
   - ✅ **Grace period**: Validates payment window
   - ✅ **Amount reasonableness**: Flags extreme values
   - ✅ **Confidence thresholds**: Color-coded scoring

6. **System Issues**
   - ✅ **Permission errors**: Handles file access issues
   - ✅ **Memory limits**: Processes efficiently
   - ✅ **Concurrent requests**: Session state management
   - ✅ **Network issues**: All processing local (no API calls)

## 🐛 Troubleshooting

### Common Issues

1. **"No module named 'streamlit'"**
   - Solution: Activate virtual environment and run `pip install -r requirements.txt`

2. **"PDF extraction failed"**
   - Solution: Check if PDF is password-protected or corrupted

3. **Low confidence scores**
   - Solution: PDF might be scanned (image-based) - OCR support coming in Phase 4

## 🚧 Future Enhancements

- [ ] OCR support for scanned PDFs (Tesseract)
  - Image preprocessing (deskew, denoise, binarize)
  - Intelligent OCR triggering
- [ ] More issuers (American Express, Standard Chartered, etc.)
- [ ] Transaction-level extraction
- [ ] Multi-file batch processing
- [ ] API endpoint

## 📝 Changelog

### v2.0 (Latest)
- ✅ Enhanced password handling (empty password attempt, hidden encryption)
- ✅ Euclidean distance-based value extraction (geometry-aware)
- ✅ Global date range fallback extraction
- ✅ Unified word box normalization (pdfplumber + OCR compatible)
- ✅ Gap-based issuer confidence scoring
- ✅ Distance-weighted candidate scoring

### v1.0 (Initial)
- ✅ Basic PDF text extraction
- ✅ 5 issuer support
- ✅ 5 field extraction
- ✅ Label-based matching
- ✅ Streamlit UI

## 📝 License

This project is for educational purposes.

## 👨‍💻 Author

Built as an assignment project for credit card statement parsing.