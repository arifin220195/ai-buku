import streamlit as st
import google.generativeai as genai
import pandas as pd

api_key = 'AIzaSyCYuuC0kFiIgl15OU65V_qVy4iYk91gbmE'
ngrok_token = '33EbqSoPnuENhYDl6dk2vC8zcLl_4G2imMgyVS6iHZSzvXQka'

# Konfigurasi API
# TIPS: Nanti kita masukkan API Key di 'Secrets' Streamlit agar aman
api_key = st.secrets["api_key"]
genai.configure(api_key=api_key)

# Membaca data lokal (yang nanti diupload ke GitHub)
df = pd.read_excel('Diskon Bazar 2025.xlsx')
df['Stok'] = 50 # Tambah stok otomatis
stok_info = df[['Judul Buku', 'Harga Normal', 'Harga Diskon', 'Stok']].to_string(index=False)

# Instruksi AI
instruction = f"Kamu asisten bazar ramah. Stok: {stok_info}. Jika pesan, minta Nama & Judul. Beri kode [ORDER: Nama | Judul]"
model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=instruction)

st.title("📚 BukuBot Bazar 2025")

# Logika Chat (Sama seperti sebelumnya)
if "messages" not in st.session_state: st.session_state.messages = []
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    response = model.generate_content(prompt)
    with st.chat_message("assistant"): st.markdown(response.text)
    st.session_state.messages.append({"role": "assistant", "content": response.text})