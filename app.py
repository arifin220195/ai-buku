import streamlit as st
import google.generativeai as genai
import pandas as pd
import os
from datetime import datetime
import json

# ============================================================================
# KONFIGURASI
# ============================================================================
try:
    api_key = st.secrets.get("api_key")
    if not api_key:
        st.error("❌ API Key tidak ditemukan. Silakan tambahkan di Streamlit Secrets.")
        st.stop()
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"❌ Error konfigurasi API: {str(e)}")
    st.stop()

# ============================================================================
# LOAD DATA
# ============================================================================
@st.cache_data
def load_buku_data():
    """Load dan validasi data buku dari CSV"""
    try:
        if not os.path.exists('buku.csv'):
            st.error("❌ File 'buku.csv' tidak ditemukan.")
            st.stop()
        
        df = pd.read_csv('buku.csv')
        
        # Validasi kolom yang diperlukan
        required_cols = ['Judul Buku', 'Harga Normal', 'Harga Diskon', 'Stock']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            st.error(f"❌ Kolom yang hilang di CSV: {', '.join(missing_cols)}")
            st.stop()
        
        # Tambah stok otomatis
        df['Stock'] = df['Stock'] + 50
        return df
    except pd.errors.EmptyDataError:
        st.error("❌ File 'buku.csv' kosong.")
        st.stop()
    except Exception as e:
        st.error(f"❌ Error membaca CSV: {str(e)}")
        st.stop()

df = load_buku_data()
stok_info = df[['Judul Buku', 'Harga Normal', 'Harga Diskon', 'Stok']].to_string(index=False)

# ============================================================================
# INISIALISASI AI MODEL
# ============================================================================
instruction = f"""Kamu adalah asisten penjual buku yang ramah dan profesional untuk Bazar Buku 2025.

INFORMASI STOK TERKINI:
{stok_info}

INSTRUKSI PENTING:
1. Berikan sambutan yang ramah dan bantu pelanggan
2. Ketika ada permintaan pembelian, minta:
   - Nama lengkap pelanggan
   - Judul buku yang ingin dibeli
   - Jumlah buku (jika lebih dari 1)
3. Verifikasi ketersediaan stok sebelum konfirmasi
4. Berikan rekomendasi buku lain jika relevan
5. Akhiri setiap order dengan format: [ORDER: Nama | Judul | Jumlah]
6. Jika stok tidak cukup, tawarkan alternatif buku serupa

LARANGAN:
- Jangan ubah harga tanpa persetujuan
- Jangan janji barang yang sudah habis
- Jangan berikan info selain tentang buku"""

try:
    model = genai.GenerativeModel(
        "gemini-1.5-flash",
        system_instruction=instruction,
        generation_config=genai.types.GenerationConfig(
            temperature=0.7,
            top_p=0.9,
            max_output_tokens=500
        )
    )
except Exception as e:
    st.error(f"❌ Error inisialisasi model: {str(e)}")
    st.stop()

# ============================================================================
# UI STREAMLIT
# ============================================================================
st.set_page_config(
    page_title="BukuBot Bazar 2025",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.title("📚 BukuBot Bazar 2025")
st.markdown("---")
st.markdown("### Selamat datang di toko buku online! 👋")

# ============================================================================
# SIDEBAR - INFO & KONTROL
# ============================================================================
with st.sidebar:
    st.header("📖 Informasi Toko")
    st.subheader("Katalog Buku Tersedia:")
    
    # Tampilkan daftar buku
    for idx, row in df.iterrows():
        with st.expander(f"📕 {row['Judul Buku']}"):
            st.write(f"**Harga Normal**: Rp {row['Harga Normal']:,.0f}")
            st.write(f"**Harga Diskon**: Rp {row['Harga Diskon']:,.0f}")
            st.write(f"**Stok Tersedia**: {row['Stok']} buku")
            if row['Stok'] < 5:
                st.warning("⚠️ Stok terbatas!")
    
    st.markdown("---")
    
    # Tombol kontrol
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh Data", key="refresh"):
            st.cache_data.clear()
            st.rerun()
    with col2:
        if st.button("🗑️ Clear Chat", key="clear"):
            st.session_state.messages = []
            st.rerun()
    
    st.markdown("---")
    st.caption("💡 Tips: Sebutkan judul buku yang ingin dibeli untuk membuat order")

# ============================================================================
# CHAT LOGIC
# ============================================================================
# Inisialisasi session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "order_count" not in st.session_state:
    st.session_state.order_count = 0

# Tampilkan chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "🤖"):
        st.markdown(msg["content"])

# Input chat
if prompt := st.chat_input("Ketik pesan Anda di sini..."):
    # Tambah pesan user ke history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)
    
    # Generate response dari AI
    try:
        with st.spinner("🤖 Bot sedang berpikir..."):
            response = model.generate_content(prompt)
            
            if not response.text:
                st.error("❌ Bot tidak bisa merespons. Coba lagi.")
            else:
                assistant_message = response.text
                
                # Deteksi order
                if "[ORDER:" in assistant_message:
                    st.session_state.order_count += 1
                
                # Tampilkan response
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(assistant_message)
                
                # Simpan ke history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_message
                })
    
    except genai.types.BlockedPromptException:
        error_msg = "⚠️ Permintaan Anda terblokir oleh safety filter. Coba dengan kata-kata yang lebih sopan."
        st.error(error_msg)
        st.session_state.messages[-1]["role"] = "error"
    
    except genai.types.StopCandidateException:
        error_msg = "⚠️ Respons bot dihentikan karena alasan keamanan. Coba pertanyaan lain."
        st.error(error_msg)
    
    except Exception as e:
        error_msg = f"❌ Error API: {str(e)}"
        st.error(error_msg)
        st.session_state.messages.pop()  # Hapus pesan user jika error

# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Pesan", len(st.session_state.messages))
with col2:
    st.metric("Total Order", st.session_state.order_count)
with col3:
    st.metric("Buku Tersedia", len(df))

st.caption(f"⏰ Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
