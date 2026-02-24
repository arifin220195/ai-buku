import streamlit as st
import google.generativeai as genai
import pandas as pd
import os
from datetime import datetime

# ============================================================================
# 1. KONFIGURASI API & MODEL (Solusi Error 404)
# ============================================================================
try:
    # Ambil API Key dari Streamlit Secrets
    api_key = st.secrets.get("api_key")
    if not api_key:
        st.error("❌ API Key tidak ditemukan. Isi 'api_key' di menu Secrets Streamlit!")
        st.stop()
    
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"❌ Error Konfigurasi: {str(e)}")
    st.stop()

# ============================================================================
# 2. LOAD DATA (Membaca buku.csv dengan kolom 'Stock')
# ============================================================================
@st.cache_data
def load_data():
    file_target = 'buku.csv'
    if os.path.exists(file_target):
        try:
            df = pd.read_csv(file_target)
            # Membersihkan spasi di nama kolom agar tidak error
            df.columns = df.columns.str.strip()
            return df
        except Exception as e:
            st.error(f"❌ Gagal membaca CSV: {e}")
            return None
    else:
        st.error(f"❌ File '{file_target}' tidak ditemukan di GitHub!")
        return None

df = load_data()

if df is not None:
    # Mengambil data untuk instruksi AI (Pastikan kolom 'Stock' sesuai CSV)
    stok_info = df[['Judul Buku', 'Harga Normal', 'Harga Diskon', 'Stock']].to_string(index=False)
    
    instruction = f"""
    Kamu adalah asisten penjualan ramah di Bazar Buku 2025.
    DATA KATALOG:
    {stok_info}
    
    TUGAS:
    - Jawab pertanyaan harga dengan ceria.
    - Jika ada yang beli, minta Nama & Judul Buku.
    - Akhiri order dengan format: [ORDER: Nama | Judul | Jumlah]
    """
    
    # PERBAIKAN ERROR 404: Gunakan 'models/gemini-1.5-flash'
    try:
        model = genai.GenerativeModel(
            model_name="models/gemini-1.5-flash",
            system_instruction=instruction
        )
    except Exception as e:
        st.error(f"❌ Error Model: {e}")
else:
    st.stop()

# ============================================================================
# 3. TAMPILAN UI STREAMLIT
# ============================================================================
st.set_page_config(page_title="BukuBot Bazar", page_icon="📚")
st.title("📚 BukuBot Bazar 2025")

# Sidebar untuk cek stok manual
with st.sidebar:
    st.header("📖 Katalog")
    for _, row in df.iterrows():
        with st.expander(f"📕 {row['Judul Buku']}"):
            st.write(f"Harga: Rp {row['Harga Diskon']:,.0f}")
            st.write(f"Stok: {row['Stock']}")

# Logika Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Munculkan chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input Chat
if prompt := st.chat_input("Tanya harga buku..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    try:
        # Generate respon AI
        response = model.generate_content(prompt)
        bot_text = response.text
        
        with st.chat_message("assistant"):
            st.markdown(bot_text)
        st.session_state.messages.append({"role": "assistant", "content": bot_text})
    except Exception as e:
        st.error(f"❌ Error AI: {str(e)}")
