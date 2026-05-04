import streamlit as st
import imagehash
import numpy as np
import sqlite3
import cv2
import pytesseract
from PIL import Image, ImageChops, ImageEnhance, ImageStat
from datetime import datetime

# --- 1. DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('canteen_vault.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS payments 
                 (hash_val TEXT PRIMARY KEY, amount TEXT, tx_id TEXT, timestamp TEXT)''')
    conn.commit()
    return conn

# --- 2. ADVANCED FORENSICS (No ML) ---

def analyze_image(img):
    # Convert PIL to OpenCv format
    open_cv_image = np.array(img.convert('RGB'))
    img_gray = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2GRAY)
    
    # 1. Improved ELA (Handles PNG by forcing a JPEG conversion)
    img_rgb = img.convert("RGB")
    temp_file = "temp_check.jpg"
    img_rgb.save(temp_file, 'JPEG', quality=85)
    resaved = Image.open(temp_file)
    diff = ImageChops.difference(img_rgb, resaved)
    ela_score = sum(ImageStat.Stat(diff).mean) / 3
    
    # 2. Adaptive Noise Check (Standard Deviation / Mean)
    # Prevents high-res vs low-res bias
    mean_brightness = np.mean(img_gray)
    std_dev = np.std(img_gray)
    adaptive_noise = std_dev / (mean_brightness + 1) # Normalization
    
    # 3. Semantic Check (OCR) - Solving Problem #5
    # Look for keywords like "Success", "Paid", "Transaction"
    ocr_text = pytesseract.image_to_string(img_gray).lower()
    keywords = ["success", "paid", "transaction", "completed", "transfer"]
    has_keywords = any(word in ocr_text for word in keywords)
    
    # 4. Histogram Spiking (Detects "Smooth" AI gradients or flat edits)
    hist = cv2.calcHist([img_gray], [0], None, [256], [0, 256])
    max_hist_peak = np.max(hist) / (img_gray.size) # Ratio of most common color
    
    return {
        "ela": ela_score,
        "noise_ratio": adaptive_noise,
        "has_text": has_keywords,
        "peak_ratio": max_hist_peak,
        "raw_text": ocr_text,
        "diff_img": diff
    }

# --- 3. STREAMLIT UI ---

st.set_page_config(page_title="Canteen Shield V2", page_icon="🛡️")
st.title("🛡️ Canteen Anti-Fraud (DSP Edition)")

conn = init_db()
c = conn.cursor()

uploaded_file = st.file_uploader("Upload Receipt", type=["jpg", "jpeg", "png"])

if uploaded_file:
    img = Image.open(uploaded_file)
    metrics = analyze_image(img)
    
    # --- PHASE 1: SMART DUPLICATE CHECK ---
    current_hash = imagehash.phash(img)
    c.execute("SELECT hash_val FROM payments")
    stored_hashes = c.fetchall()
    
    is_duplicate = False
    # Stricter threshold (3) to combat pHash bypass attempts
    for (h_str,) in stored_hashes:
        if (current_hash - imagehash.hex_to_hash(h_str)) < 3:
            is_duplicate = True; break

    # --- PHASE 2: CALCULATE AGGREGATE TRUST ---
    trust_score = 100
    reasons = []

    if is_duplicate:
        trust_score -= 100
        reasons.append("Duplicate detected in database.")
    
    if not metrics["has_text"]:
        trust_score -= 50
        reasons.append("No payment keywords found (Non-receipt image).")
        
    if metrics["ela"] > 6.0: # High editing
        trust_score -= 30
        reasons.append("High pixel inconsistency (Possible edit).")
        
    if metrics["peak_ratio"] > 0.15: # Too much of a single flat color
        trust_score -= 20
        reasons.append("Abnormal color flatness (Possible fake/UI clone).")

    # --- DISPLAY RESULTS ---
    col1, col2 = st.columns(2)
    with col1:
        st.image(img, caption="Uploaded Image")
    with col2:
        # Scale ELA for visibility
        scale = 255.0 / (sum(ImageStat.Stat(metrics["diff_img"]).extrema[0]) + 1)
        ela_viz = ImageEnhance.Brightness(metrics["diff_img"]).enhance(scale)
        st.image(ela_viz, caption="Forensic Heatmap")

    st.subheader(f"Trust Score: {max(0, trust_score)}/100")
    
    if trust_score >= 80:
        st.success("✅ Payment appears authentic.")
    elif trust_score >= 40:
        st.warning(f"⚠️ Suspicious: {', '.join(reasons)}")
    else:
        st.error(f"❌ Rejected: {', '.join(reasons)}")

    # Record data
    if st.button("Verify & Archive"):
        c.execute("INSERT INTO payments VALUES (?, ?, ?, ?)", 
                  (str(current_hash), "Unknown", "Extracted", datetime.now()))
        conn.commit()
        st.success("Archived for audit.")