import streamlit as st
import networkx as nx
import pandas as pd
from streamlit_js_eval import streamlit_js_eval

# ==============================================================================
# 1. KONFIGURASI HALAMAN WEB 
# ==============================================================================
st.set_page_config(
    page_title="AI Drop Core Optimizer", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

st.title("⚡ AI-Based Drop Core Cable Route Optimizer")
st.write("Sistem Cerdas Rekomendasi Jalur Kabel FTTH - PT DARIA PRATAMA MANDIRI.")
st.markdown("---")

# ==============================================================================
# 2. INISIALISASI DATA STATE (MEMORI PENYIMPANAN DATA MULTI-TITIK)
# ==============================================================================
if 'daftar_rumah' not in st.session_state:
    st.session_state['daftar_rumah'] = []

# Tiang ODP Pusat Tetap milik perusahaan (Sebagai Parameter Pusat)
LAT_ODP_PUSAT = -7.6405
LON_ODP_PUSAT = 112.9010

# ==============================================================================
# 3. PANEL KONTROL INPUT & LIVE GEOTAGGING GPS HP (MULTI-INPUT & BEBAS BUG)
# ==============================================================================
st.sidebar.header("📍 Fitur Survei Lapangan & GPS")

# Tombol Sinkronisasi GPS HP Anda secara instan
lokasi_mentah = streamlit_js_eval(
    js_expressions="new Promise((resolve) => { navigator.geolocation.getCurrentPosition((pos) => { resolve([pos.coords.latitude, pos.coords.longitude]) }, (err) => { resolve(null) }, { enableHighAccuracy: true, timeout: 5000 }) })", 
    want_output=True, 
    key="gps_tracker_core"
)

# Ambil koordinat GPS riil atau pasang simulator aman jika sinyal lemah
if lokasi_mentah and isinstance(lokasi_mentah, list) and len(lokasi_mentah) == 2:
    lat_sekarang = float(lokasi_mentah[0])
    lon_sekarang = float(lokasi_mentah[1])
    st.sidebar.success(f"🟢 GPS Terkunci: {lat_sekarang:.5f}, {lon_sekarang:.5f}")
else:
    lat_sekarang = -7.6432
    lon_sekarang = 112.9055
    st.sidebar.warning("📡 Menggunakan Mode Koordinat Default Wilayah.")

# Input Form untuk menambahkan Banyak Titik Rumah Pelanggan
st.sidebar.markdown("### ➕ Tambah Titik Rumah")
nama_user = st.sidebar.text_input("Nama Pelanggan Baru:", placeholder="Contoh: Rumah Budi")
input_lat = st.sidebar.number_input("Latitude:", value=lat_sekarang, format="%.6f")
input_lon = st.sidebar.number_input("Longitude:", value=lon_sekarang, format="%.6f")

if st.sidebar.button("💾 Simpan Titik Lokasi Ini", use_container_width=True):
    if nama_user:
        st.session_state['daftar_rumah'].append({
            'Nama': nama_user,
            'lat': input_lat,
            'lon': input_lon
        })
        st.sidebar.success(f"Berhasil menyimpan lokasi {nama_user}!")
    else:
        st.sidebar.error("Nama pelanggan wajib diisi!")

# Tombol untuk mereset seluruh data survei
if st.sidebar.button("🗑️ Reset Semua Titik", type="secondary", use_container_width=True):
    st.session_state['daftar_rumah'] = []
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("🧠 Parameter Algoritma AI")
penalti_belokan = st.sidebar.slider("Faktor Penalti Belokan Kabel (dBm):", 0.0, 1.0, 0.5, step=0.1)
hindari_pohon = st.sidebar.checkbox("Hindari Jalur Pohon Rimbun", value=True)

hitung_tombol = st.sidebar.button("ANALISIS JALUR TERBAIK 🤖", type="primary", use_container_width=True)

# ==============================================================================
# 4. PROSES MULTI-JALUR DENGAN ALGORITMA AI & ESTIMASI LOSS BUDGET
# ==============================================================================
# Siapkan DataFrame untuk plotting peta terpadu
map_data = [{'lat': LAT_ODP_PUSAT, 'lon': LON_ODP_PUSAT, 'Nama': 'ODP_Pusat_Daria', 'Tipe': 'ODP Utama'}]

if hitung_tombol:
    if len(st.session_state['daftar_rumah']) == 0:
        st.error("Silakan masukkan minimal satu titik lokasi rumah pelanggan di menu samping sebelum memulai analisis AI!")
    else:
        st.subheader("📋 Hasil Analisis Distribusi Kabel FTTH")
        
        # Inisialisasi Graf Kosong
        G = nx.Graph()
        G.add_node('ODP_Pusat_Daria')
        
        # Tambahkan semua rumah terdaftar ke dalam kalkulator AI
        for data in st.session_state['daftar_rumah']:
            nama = data['Nama']
            G.add_node(nama)
            
            # Hitung estimasi jarak geometris sederhana dari ODP ke Rumah User
            dx = (data['lat'] - LAT_ODP_PUSAT) * 111000 # konversi derajat ke meter
            dy = (data['lon'] - LON_ODP_PUSAT) * 111000
            jarak_asli = math.sqrt(dx**2 + dy**2)
            
            # Hitung penalti rintangan di lapangan
            bobot_ai = jarak_asli + (penalti_belokan * 10)
            if hindari_pohon:
                bobot_ai += 15 # Tambah bobot hambatan virtual
                
            G.add_edge('ODP_Pusat_Daria', nama, jarak=jarak_asli, bobot=bobot_ai)
            
            # Eksekusi pencarian rute terpendek oleh modul AI
            rute = nx.shortest_path(G, source='ODP_Pusat_Daria', target=nama, weight='bobot')
            
            # Estimasi rumus redaman daya optik link
            loss_kabel = jarak_asli * 0.0035
            total_redaman = -(19.0 + loss_kabel + 0.6)
            
            # Kategori status keamanan redaman
            status = "🟢 AMAN" if total_redaman >= -23.0 else "🟡 WARNING" if total_redaman >= -26.0 else "🔴 LOS"
            
            # Tampilkan kartu metrik per pelanggan
            st.info(f"👤 **Pelanggan: {nama}**")
            c1, c2, c3 = st.columns(3)
            c1.write(f"📏 **Panjang Bentangan:** {jarak_asli:.1f} Meter")
            c2.write(f"📉 **Estimasi Redaman:** {total_redaman:.2f} dBm")
            c3.write(f"🚨 **Status Kelayakan:** {status}")
            
            # Simpan data ke koordinat untuk pemetaan visual
            map_data.append({'lat': data['lat'], 'lon': data['lon'], 'Nama': nama, 'Tipe': 'Rumah Pelanggan'})

# ==============================================================================
# 5. TAMPILAN PETA INTERAKTIF TERINTEGRASI (ANTI-CRASH PADA HP)
# ==============================================================================
st.subheader("🗺️ Peta Bentangan Jaringan Distribusi Kabel")

# Masukkan data rumah simulasi jika data lapangan belum tersimpan
if len(st.session_state['daftar_rumah']) == 0 and not hitung_tombol:
    map_data.append({'lat': lat_sekarang, 'lon': lon_sekarang, 'Nama': 'Simulasi Posisi Anda', 'Tipe': 'Simulator'})

df_peta = pd.DataFrame(map_data)
st.map(df_peta, latitude='lat', longitude='lon', size=20)
st.caption("Keterangan Titik Peta: Titik koordinat terpusat menunjukkan lokasi ODP Utama Daria dan sebaran seluruh rumah pelanggan yang sukses di-tagging.")