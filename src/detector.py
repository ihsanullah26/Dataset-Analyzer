import streamlit as st
import imagehash
import numpy as np
import sqlite3
from PIL import Image, ImageChops, ImageEnhance, ImageStat
from datetime import datetime

# --- 1. DATABASE LOGIC ---
def init_db():
    conn = sqlite3.connect('canteen_payments.db')
    c = conn.cursor()
    # Stores the unique hash of every approved screenshot to prevent Scenario 1
    c.execute('''CREATE TABLE IF NOT EXISTS processed_payments 
                 (hash_val TEXT PRIMARY KEY, timestamp TEXT)''')
    conn.commit()
    return conn

# --- 2. FORENSIC MATH FUNCTIONS ---

def get_fraud_score(img):
    """
    Calculates a fraud score based on image statistics.
    Real screenshots have 'sensor noise' and consistent compression.
    AI/Edited images have 'unnatural smoothness' or 'compression spikes'.
    """
    # A. Error Level Analysis (ELA) - Detects digital splicing
    img_rgb = img.convert("RGB")
    img_rgb.save("temp_resave.jpg", "JPEG", quality=90)
    resaved = Image.open("temp_resave.jpg")
    diff = ImageChops.difference(img_rgb, resaved)
    extrema = diff.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    scale = 255.0 / (max_diff if max_diff > 0 else 1)
    ela_img = ImageEnhance.Brightness(diff).enhance(scale)
    
    # Calculate ELA Intensity (Higher = more likely edited)
    stat_ela = ImageStat.Stat(diff)
    ela_score = sum(stat_ela.mean) / 3
    
    # B. Noise Profile (Standard Deviation)
    # AI renders are often too 'clean'. Real screens have sub-pixel variance.
    img_gray = img.convert("L")
    noise_score = np.std(np.array(img_gray))
    
    return ela_score, noise_score, ela_img

# --- 3. STREAMLIT UI ---

st.set_page_config(page_title="Canteen Guard v1.0", layout="wide")
st.title("🛡️ University Canteen: Payment Verifier")
st.markdown("### Detects AI Fakes & Recycled Screenshots")

conn = init_db()
c = conn.cursor()

# Sidebar for admin history
with st.sidebar:
    st.header("Admin Records")
    if st.button("Clear History (Reset DB)"):
        c.execute("DELETE FROM processed_payments")
        conn.commit()
        st.success("History Cleared!")

# Main Upload Area
uploaded_file = st.file_uploader("Upload Student's Screenshot (EasyPaisa, JazzCash, SadaPay, etc.)", type=["jpg", "jpeg", "png"])

if uploaded_file:
    img = Image.open(uploaded_file)
    
    # --- PHASE 1: DUPLICATE DETECTION (Scenario 1) ---
    p_hash = str(imagehash.phash(img))
    c.execute("SELECT * FROM processed_payments WHERE hash_val=?", (p_hash,))
    duplicate_record = c.fetchone()

    if duplicate_record:
        st.error(f"🚨 FAKE DETECTED (RECYCLED): This exact screenshot was already used on {duplicate_record[1]}.")
        st.warning("Action: Do not provide food. Ask for a fresh payment.")
    
    else:
        # --- PHASE 2: AI & EDIT DETECTION (Scenario 2) ---
        with st.spinner("Analyzing Pixel Integrity..."):
            ela_val, noise_val, ela_display = get_fraud_score(img)
            
            # Mathematical Thresholds
            # 1. High ELA (> 5.0) means numbers/text were likely altered.
            # 2. Low Noise (< 45.0) suggests an AI-generated smooth image.
            
            is_edited = ela_val > 5.5
            is_ai_generated = noise_val < 42.0
            
            # Combine into a final "Authenticity Score"
            # We start at 100 and subtract points for anomalies
            auth_score = 100
            if is_edited: auth_score -= 40
            if is_ai_generated: auth_score -= 30
            
            # UI Feedback
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Authenticity Score")
                if auth_score >= 80:
                    st.success(f"✅ SCORE: {int(auth_score)}/100 (Looks Real)")
                elif auth_score >= 50:
                    st.warning(f"⚠️ SCORE: {int(auth_score)}/100 (Suspicious)")
                else:
                    st.error(f"❌ SCORE: {int(auth_score)}/100 (Likely Fake)")
                
                st.image(img, caption="Original Screenshot", use_container_width=True)

            with col2:
                st.subheader("Forensic View")
                st.image(ela_display, caption="Compression Analysis (White glows indicate edits)", use_container_width=True)
                
                st.write("**Mathematical Breakdown:**")
                st.write(f"- Edit Intensity: `{ela_val:.2f}` (Safe < 5.5)")
                st.write(f"- Pixel Noise: `{noise_val:.2f}` (Safe > 45.0)")

        # Approval Logic
        if st.button("Confirm Payment & Serve Food"):
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            c.execute("INSERT INTO processed_payments VALUES (?, ?)", (p_hash, current_time))
            conn.commit()
            st.balloons()
            st.success("Payment recorded! This image cannot be used again.")