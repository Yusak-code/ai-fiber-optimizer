import streamlit as st
import pandas as pd
import math
from streamlit_js_eval import streamlit_js_eval

# ==============================================================================
# 1. KONFIGURASI UTAMA HALAMAN WEB (RESPONSIF HP)
# ==============================================================================
st.set_page_config(
    page_title="AI Drop Core Optimizer", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

st.title("⚡ FTTH Network Geotagging & Route Survey")
st.write("Aplikasi Manajemen Mapping Riil Lapangan (ODP, Tiang Tumpuan, & Rumah Pelanggan) - PT DARIA PRATAMA MANDIRI.")
st.markdown("---")

# ==============================================================================
# 2. MANAGEMEN STATE MEMORI STREAMLIT (ANTI-RESET SAAT DIKLIK)
# ==============================================================================
if 'titik_jaringan' not in st.session_state:
    st.session_state['titik_jaringan'] = []

# ==============================================================================
# 3. FITUR UTAMA LIVE TRACKING GPS HP SENSOR
# ==============================================================================
st.sidebar.header("📡 Modul Sensor GPS HP")

# Memanggil API Geolocation dengan pembatasan timeout asinkronus (Mencegah Bug/Crash)
koordinat_mentah = streamlit_js_eval(
    js_expressions="new Promise((resolve) => { navigator.geolocation.getCurrentPosition((pos) => { resolve([pos.coords.latitude, pos.coords.longitude]) }, (err) => { resolve(null) }, { enableHighAccuracy: true, timeout: 5000 }) })", 
    want_output=True, 
    key="sensor_gps_ftth_field"
)

# Validasi pembacaan data koordinat GPS
if koordinat_mentah and isinstance(koordinat_mentah, list) and len(koordinat_mentah) == 2:
    lat_sekarang = float(koordinat_mentah[0])
    lon_sekarang = float(koordinat_mentah[1])
    st.sidebar.success(f"🟢 GPS Terkunci: {lat_sekarang:.5f}, {lon_sekarang:.5f}")
else:
    # Koordinat fallback standar wilayah Pasuruan jika di dalam ruangan/sinyal lemah
    lat_sekarang = -7.64320
    lon_sekarang = 112.90550
    st.sidebar.warning("⚠️ Satelit Lemah. Menggunakan Simulator Koordinat.")

# Tombol untuk memaksa refresh permintaan izin browser
st.sidebar.button("🔄 Segarkan / Refresh GPS", use_container_width=True)

# ==============================================================================
# 4. KONTROL FORM INPUT MULTI-TAGGING (ODP, TIANG, RUMAH)
# ==============================================================================
st.sidebar.markdown("---")
st.sidebar.subheader("➕ Formulir Tagging Titik Objek")

# Dropdown pemilihan jenis tagging sesuai kebutuhan lapangan Anda
tipe_objek = st.sidebar.selectbox(
    "Pilih Tipe Objek Lapangan:",
    ["🏠 Rumah Pelanggan", "🔴 Titik ODP", "🪵 Tiang Tumpuan Kabel"]
)

nama_titik = st.sidebar.text_input("Label / Nama Titik:", placeholder="Contoh: Tiang No 4 / ODP A1")
lat_input = st.sidebar.number_input("Garis Latitude (Lintang):", value=lat_sekarang, format="%.6f")
lon_input = st.sidebar.number_input("Garis Longitude (Bujur):", value=lon_sekarang, format="%.6f")

# Proses Penyimpanan Banyak Titik Sekaligus
if st.sidebar.button("💾 Simpan & Plot Titik Objek", type="primary", use_container_width=True):
    if nama_titik:
        # Menentukan ukuran dot dan warna di peta berdasarkan tipenya
        if "ODP" in tipe_objek:
            warna_hex = "#ff0000"  # Merah untuk ODP
            skala_ukuran = 120
        elif "Tiang" in tipe_objek:
            warna_hex = "#808080"  # Abu-abu untuk Tiang Tumpuan
            skala_ukuran = 60
        else:
            warna_hex = "#0000ff"  # Biru untuk Rumah Pelanggan
            skala_ukuran = 90
            
        st.session_state['titik_jaringan'].append({
            "Nama / ID": nama_titik,
            "Kategori": tipe_objek,
            "lat": lat_input,
            "lon": lon_input,
            "color": warna_hex,
            "size": skala_ukuran
        })
        st.toast(f"Berhasil menyimpan {tipe_objek}: {nama_titik}!", icon="✅")
    else:
        st.sidebar.error("Kolom Nama/Label wajib diisi!")

# Tombol Reset Data
if st.sidebar.button("🗑️ Kosongkan Semua Data Survei", type="secondary", use_container_width=True):
    st.session_state['titik_jaringan'] = []
    st.rerun()

# ==============================================================================
# 5. PEMROSESAN ANALISIS DATA METRIK LINK (ALGORITMA & LOSS BUDGET)
# ==============================================================================
st.subheader("📊 Dasbor Informasi Survei Lapangan")

if len(st.session_state['titik_jaringan']) > 0:
    df_visual = pd.DataFrame(st.session_state['titik_jaringan'])
    
    # Tampilkan tabel log data survey lapangan yang scannable
    st.dataframe(df_visual[["Nama / ID", "Kategori", "lat", "lon"]], use_container_width=True)
    
    # Hitung Estimasi Bentangan Total jika minimal ada 2 titik yang di-tagging
    if len(st.session_state['titik_jaringan']) >= 2:
        total_jarak_tarikan = 0.0
        for i in range(len(st.session_state['titik_jaringan']) - 1):
            p1 = st.session_state['titik_jaringan'][i]
            p2 = st.session_state['titik_jaringan'][i+1]
            # Rumus matematis jarak phytagoras koordinat ke satuan meter
            dx = (p1['lat'] - p2['lat']) * 111320
            dy = (p1['lon'] - p2['lon']) * 111320
            total_jarak_tarikan += math.sqrt(dx**2 + dy**2)
            
        # Hitung kalkulasi redaman teknis
        loss_kabel_optik = total_jarak_tarikan * 0.0035
        estimasi_redaman_dbm = -(19.0 + loss_kabel_optik + 0.6)
        
        status_kelayakan = "🟢 AMAN (Redaman Sangat Bagus)" if estimasi_redaman_dbm >= -23.0 else "🟡 WARNING (Batas Toleransi)" if estimasi_redaman_dbm >= -27.0 else "🔴 LOS / CRITICAL"
        
        # Tampilkan ringkasan data teknis konstruksi
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Panjang Drop Core", f"{total_jarak_tarikan:.2f} Meter")
        c2.metric("Estimasi Redaman Ujung Rumah", f"{estimasi_redaman_dbm:.2f} dBm")
        c3.metric("Status Kelayakan Jalur", status_kelayakan)
else:
    st.info("💡 Belum ada data titik lapangan yang disimpan. Silakan lakukan tagging ODP, Tiang, dan Rumah Pelanggan di menu sebelah kiri terlebih dahulu.")

# ==============================================================================
# 6. VISUALISASI PETA RIIL LAPANGAN DIGITAL (ANTI-BUG / ANTI-FREEZE)
# ==============================================================================
st.markdown("<br>", unsafe_allow_html=True)
st.subheader("🗺️ Visualisasi Peta Titik Tarikan Kabel Jaringan")

if len(st.session_state['titik_jaringan']) > 0:
    # Menggunakan df_visual dari database session state yang sudah diverifikasi
    st.map(df_visual, latitude="lat", longitude="lon", color="color", size="size")
    st.caption("🔴 Titik Merah Besar = ODP Utama | 🪵 Titik Abu-Abu = Tiang Tumpuan | 🏠 Titik Biru = Rumah Pelanggan.")
else:
    # Tampilkan peta kosong dengan marker simulator di awal aplikasi agar user tidak bingung
    data_kosong = pd.DataFrame([{"lat": lat_sekarang, "lon": lon_sekarang, "color": "#00ff00", "size": 50}])
    st.map(data_kosong, latitude="lat", longitude="lon", color="color", size="size")
    st.caption("Peta siap menerima data penandaan koordinat dari smartphone teknisi PT DARIA PRATAMA MANDIRI.")