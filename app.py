# app.py - Refined UI
import io
import json
import streamlit as st
import pikepdf
from parser import parse_pdf

st.set_page_config(page_title="Credit Card Statement Parser", layout="wide")

# Header
st.title("Credit Card Statement Parser")
st.caption("Supports IDFC • HDFC • SBI • Axis • ICICI")

uploaded_files = st.file_uploader(
    "Upload PDF Statement(s)", 
    type=["pdf"], 
    accept_multiple_files=True,
    help="Select one or more credit card statement PDFs"
)

def is_encrypted(raw_bytes: bytes) -> bool:
    """Check if PDF is password protected."""
    try:
        with pikepdf.open(io.BytesIO(raw_bytes)) as pdf:
            pass
        return False
    except pikepdf.PasswordError:
        return True
    except Exception as e:
        st.warning(f"Could not verify PDF encryption status: {e}")
        return False

def test_password(raw_bytes: bytes, password: str) -> tuple[bool, str]:
    """
    Test if password works for the PDF.
    Returns (success, error_message)
    """
    try:
        with pikepdf.open(io.BytesIO(raw_bytes), password=password) as pdf:
            pass
        return True, ""
    except pikepdf.PasswordError:
        return False, "Incorrect password"
    except Exception as e:
        return False, f"Error: {str(e)}"

if uploaded_files:
    for file_idx, f in enumerate(uploaded_files):
        with st.container(border=True):
            st.subheader(f.name)
            
            # Read file bytes once
            raw_bytes = f.read()
            
            # Check if encrypted
            is_pw_protected = is_encrypted(raw_bytes)
            
            # Session state keys for this file
            pw_key = f"password_{file_idx}_{f.name}"
            pw_verified_key = f"pw_verified_{file_idx}_{f.name}"
            pw_attempts_key = f"pw_attempts_{file_idx}_{f.name}"
            
            password = None
            
            if is_pw_protected:
                # Initialize attempt counter
                if pw_attempts_key not in st.session_state:
                    st.session_state[pw_attempts_key] = 0
                
                # Check if password already verified
                if not st.session_state.get(pw_verified_key, False):
                    st.warning("This PDF is password protected")
                    
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        entered_pw = st.text_input(
                            "Password",
                            type="password",
                            key=f"input_{pw_key}",
                            placeholder="Enter password"
                        )
                    
                    with col2:
                        st.write("")
                        st.write("")
                        verify_clicked = st.button("Unlock", key=f"verify_{pw_key}", type="primary")
                    
                    if verify_clicked and entered_pw:
                        with st.spinner("Verifying..."):
                            success, error_msg = test_password(raw_bytes, entered_pw)
                            
                            if success:
                                st.session_state[pw_key] = entered_pw
                                st.session_state[pw_verified_key] = True
                                st.session_state[pw_attempts_key] = 0
                                st.success("Password verified")
                                st.rerun()
                            else:
                                st.session_state[pw_attempts_key] += 1
                                attempts = st.session_state[pw_attempts_key]
                                st.error(f"{error_msg} (Attempt {attempts})")
                    
                    if st.session_state[pw_attempts_key] > 0:
                        st.caption(f"Failed attempts: {st.session_state[pw_attempts_key]}")
                    
                    continue  # Don't process until password verified
                else:
                    # Password already verified
                    password = st.session_state.get(pw_key)
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.success("PDF unlocked")
                    with col2:
                        if st.button("Clear password", key=f"lock_{pw_key}"):
                            del st.session_state[pw_key]
                            del st.session_state[pw_verified_key]
                            st.rerun()
            
            # Parse the PDF
            with st.spinner("Parsing statement..."):
                try:
                    result = parse_pdf(io.BytesIO(raw_bytes), password=password, filename=f.name)
                except Exception as e:
                    st.error(f"Error parsing PDF: {str(e)}")
                    continue
            
            if not result.get("success"):
                error_msg = result.get('error', 'Unknown error occurred')
                st.error(error_msg)
                
                # If password error, clear verification
                if is_pw_protected and ("password" in error_msg.lower() or "encrypted" in error_msg.lower()):
                    if pw_verified_key in st.session_state:
                        del st.session_state[pw_verified_key]
                    if st.button("Re-enter password", key=f"retry_{pw_key}"):
                        if pw_key in st.session_state:
                            del st.session_state[pw_key]
                        if pw_verified_key in st.session_state:
                            del st.session_state[pw_verified_key]
                        st.rerun()
                continue
            
            # Display results
            issuer = result.get("issuer") or "UNKNOWN"
            conf = int(100 * (result.get("issuer_confidence") or 0.0))
            
            st.markdown(f"**Detected Issuer:** {issuer} ({conf}% confidence)")
            
            records = result.get("records", [])
            if not records:
                st.warning("No card records found in this statement")
                continue
            
            # Display each card record
            for i, rec in enumerate(records, 1):
                card_mask = rec.get('card_mask', '(unknown)')
                st.markdown(f"#### Card {i} — {card_mask}")
                
                c1, c2, c3 = st.columns(3)
                c4, c5 = st.columns(2)
                
                def show_field(col, label, key, is_money=False):
                    val = rec.get(key)
                    conf = rec.get("confidence", {}).get(key, 0.0)
                    page = rec.get("evidence", {}).get(key, {}).get("page")
                    
                    conf_pct = int(conf * 100) if val is not None else 0
                    
                    with col:
                        st.markdown(f"**{label}**")
                        
                        if val is None:
                            st.markdown("*Not found*")
                        else:
                            shown = f"₹{val:,.2f}" if is_money else str(val)
                            st.markdown(f"### {shown}")
                        
                        # Confidence indicator
                        if conf_pct >= 90:
                            st.progress(conf_pct / 100, text=f"Confidence: {conf_pct}%")
                        elif conf_pct >= 70:
                            st.progress(conf_pct / 100, text=f"Confidence: {conf_pct}%")
                        elif conf_pct > 0:
                            st.progress(conf_pct / 100, text=f"Low confidence: {conf_pct}%")
                        else:
                            st.progress(0, text="Not detected")
                        
                        if page:
                            st.caption(f"Page {page}")
                
                show_field(c1, "Card Last 4", "card_last", is_money=False)
                show_field(c2, "Payment Due Date", "payment_due_date")
                show_field(c3, "Total Amount Due", "total_amount_due", is_money=True)
                show_field(c4, "Minimum Amount Due", "minimum_amount_due", is_money=True)
                show_field(c5, "Available Credit Limit", "available_credit_limit", is_money=True)
                
                # Evidence section
                with st.expander("View extraction details"):
                    evidence = rec.get("evidence", {})
                    if evidence:
                        st.json(evidence)
                    else:
                        st.caption("No evidence data available")
                
                if i < len(records):
                    st.divider()

# Footer
st.markdown("---")
st.caption("All processing is done locally. Passwords are used in memory only and never stored.")