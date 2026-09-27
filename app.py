import streamlit as st
import pandas as pd
import math
from streamlit_js_eval import streamlit_js_eval

# ==============================================================================
# 1. KONFIGURASI UTAMA HALAMAN WEB (RESPONSIF HP)
# ==============================================================================
st.set_page_config(
    page_title="AI Multi-Route & RAB Optimizer", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

st.title("⚡ FTTH Multi-Route & RAB Cost Comparison Analysis")
st.write("Sistem Cerdas Perbandingan Jalur Alternatif & Rencana Anggaran Biaya (RAB) Drop Core - PT DARIA PRATAMA MANDIRI.")
st.markdown("---")

# ==============================================================================
# 2. MANAGEMEN STATE MEMORI STREAMLIT (ANTI-RESET)
# ==============================================================================
if 'titik_jaringan' not in st.session_state:
    st.session_state['titik_jaringan'] = []

# ==============================================================================
# 3. FITUR UTAMA LIVE TRACKING GPS HP SENSOR
# ==============================================================================
st.sidebar.header("📡 Modul Sensor GPS HP")

koordinat_mentah = streamlit_js_eval(
    js_expressions="new Promise((resolve) => { navigator.geolocation.getCurrentPosition((pos) => { resolve([pos.coords.latitude, pos.coords.longitude]) }, (err) => { resolve(null) }, { enableHighAccuracy: true, timeout: 5000 }) })", 
    want_output=True, 
    key="sensor_gps_rab_optimizer"
)

if koordinat_mentah and isinstance(koordinat_mentah, list) and len(koordinat_mentah) == 2:
    lat_sekarang = float(koordinat_mentah[0])
    lon_sekarang = float(koordinat_mentah[1])
    st.sidebar.success(f"🟢 GPS Terkunci: {lat_sekarang:.5f}, {lon_sekarang:.5f}")
else:
    lat_sekarang = -7.64320
    lon_sekarang = 112.90550
    st.sidebar.warning("⚠️ Menggunakan Simulator Koordinat.")

st.sidebar.button("🔄 Segarkan / Refresh GPS", use_container_width=True)

# ==============================================================================
# 4. FITUR BARU: INPUT STANDAR HARGA MATERIAL & JASA (UNTUK RAB)
# ==============================================================================
st.sidebar.markdown("---")
st.sidebar.subheader("💰 Standar Harga Satuan Lapangan")
harga_kabel_per_meter = st.sidebar.number_input("Harga Kabel Drop Core / Meter (Rp):", value=1500, step=100)
harga_tiang_per_titik = st.sidebar.number_input("Biaya Aksesoris & Jasa per Tiang (Rp):", value=50000, step=5000)

# ==============================================================================
# 5. KONTROL FORM INPUT MULTI-JALUR & MULTI-TAGGING
# ==============================================================================
st.sidebar.markdown("---")
st.sidebar.subheader("➕ Formulir Penandaan Jalur")

pilihan_jalur = st.sidebar.selectbox(
    "Kelompokkan ke Jalur:",
    ["Jalur Alternatif A (Utama)", "Jalur Alternatif B (Cadangan)", "Jalur Alternatif C"]
)

tipe_objek = st.sidebar.selectbox(
    "Pilih Tipe Objek:",
    ["🏠 Rumah Pelanggan", "🔴 Titik ODP", "🪵 Tiang Tumpuan Kabel"]
)

nama_titik = st.sidebar.text_input("Label / Nama Titik:", placeholder="Contoh: Tiang 1 / ODP A")
lat_input = st.sidebar.number_input("Garis Latitude (Lintang):", value=lat_sekarang, format="%.6f")
lon_input = st.sidebar.number_input("Garis Longitude (Bujur):", value=lon_sekarang, format="%.6f")

if st.sidebar.button("💾 Simpan & Plot ke Rute", type="primary", use_container_width=True):
    if nama_titik:
        if "ODP" in tipe_objek:
            warna_hex = "#ff0000"  # Merah
            skala_ukuran = 120
        elif "Tiang" in tipe_objek:
            warna_hex = "#808080"  # Abu-abu
            skala_ukuran = 60
        else:
            warna_hex = "#0000ff"  # Biru
            skala_ukuran = 90
            
        st.session_state['titik_jaringan'].append({
            "Jalur": pilihan_jalur,
            "Nama / ID": nama_titik,
            "Kategori": tipe_objek,
            "lat": lat_input,
            "lon": lon_input,
            "color": warna_hex,
            "size": skala_ukuran
        })
        st.toast(f"Berhasil menyimpan {nama_titik} ke {pilihan_jalur}!", icon="✅")
    else:
        st.sidebar.error("Kolom Nama/Label wajib diisi!")

if st.sidebar.button("🗑️ Kosongkan Semua Data Rute", type="secondary", use_container_width=True):
    st.session_state['titik_jaringan'] = []
    st.rerun()

# ==============================================================================
# 6. KOMPARASI TEKNIS & ANALISIS RAB JALUR ALTERNATIF (AI DECISION)
# ==============================================================================
st.subheader("📊 Analisis Komparasi Teknis & Rencana Anggaran Biaya (RAB)")

if len(st.session_state['titik_jaringan']) > 0:
    df_visual = pd.DataFrame(st.session_state['titik_jaringan'])
    
    ringkasan_rute = []
    jalur_unik = df_visual['Jalur'].unique()
    
    for jl in jalur_unik:
        df_sub = df_visual[df_visual['Jalur'] == jl].reset_index(drop=True)
        total_tiang = len(df_sub[df_sub['Kategori'] == "🪵 Tiang Tumpuan Kabel"])
        
        jarak_rute = 0.0
        if len(df_sub) >= 2:
            for i in range(len(df_sub) - 1):
                p1 = df_sub.iloc[i]
                p2 = df_sub.iloc[i+1]
                dx = (p1['lat'] - p2['lat']) * 111320
                dy = (p1['lon'] - p2['lon']) * 111320
                jarak_rute += math.sqrt(dx**2 + dy**2)
        
        # 1. Rumus Estimasi Redaman Fisik Kabel
        loss_kabel = jarak_rute * 0.0035
        estimasi_dbm = -(19.0 + loss_kabel + 0.6 + (total_tiang * 0.1))
        status_jalur = "🟢 AMAN" if estimasi_dbm >= -23.0 else "🟡 WARNING" if estimasi_dbm >= -27.0 else "🔴 LOS"
        
        # 2. Rumus Fitur Baru: Perhitungan Nilai RAB Material & Jasa Lapangan
        total_biaya_kabel = jarak_rute * harga_kabel_per_meter
        total_biaya_tiang = total_tiang * harga_tiang_per_titik
        total_rab_konstruksi = total_biaya_kabel + total_biaya_tiang
        
        ringkasan_rute.append({
            "Nama Rute": jl,
            "Total Panjang Drop Core": f"{jarak_rute:.1f} Meter",
            "Jumlah Tiang Tumpuan": f"{total_tiang} Titik",
            "Prediksi Redaman Akhir": f"{estimasi_dbm:.2f} dBm",
            "Kelayakan Jalur": status_jalur,
            "Estimasi Total RAB": f"Rp {total_rab_konstruksi:,.0f}",
            "rab_angka": total_rab_konstruksi,
            "dbm_angka": estimasi_dbm
        })
    
    df_perbandingan = pd.DataFrame(ringkasan_rute)
    
    # Rekomendasi Keputusan AI (Mencari Kombinasi Biaya Paling Murah & Redaman Paling Aman)
    if not df_perbandingan.empty:
        # Filter jalur yang tidak LOS terlebih dahulu (di atas -27 dBm)
        jalur_layak = df_perbandingan[df_perbandingan['dbm_angka'] >= -27.0]
        if not jalur_layak.empty:
            # Cari yang biaya konstruksinya (RAB) paling ekonomis
            jalur_terbaik = jalur_layak.sort_values(by="rab_angka").iloc[0]
            st.success(f"🤖 **Rekomendasi Keputusan AI:** Direkomendasikan menggunakan **{jalur_terbaik['Nama Rute']}**. Jalur ini memberikan efisiensi anggaran terbaik (**{jalur_terbaik['Estimasi Total RAB']}**) dengan kualitas redaman yang laik jalan (**{jalur_terbaik['Prediksi Redaman Akhir']}**).")
        else:
            st.error("⚠️ Semua jalur alternatif yang di-tagging memiliki redaman terlalu tinggi (🔴 LOS). Silakan cari jalur tiang tumpuan lain yang lebih pendek.")

    # Tampilkan tabel perbandingan menyeluruh beserta kolom RAB
    st.dataframe(df_perbandingan.drop(columns=['rab_angka', 'dbm_angka']), use_container_width=True)
    
    # Daftar Log Koordinat Mentah
    with st.expander("👁️ Lihat Detail Log Titik Koordinat Semua Jalur"):
        st.dataframe(df_visual[["Jalur", "Nama / ID", "Kategori", "lat", "lon"]], use_container_width=True)

else:
    st.info("💡 Belum ada rute jalur yang di-tagging. Silakan lakukan survei dan simpan koordinat di panel menu sebelah kiri.")

# ==============================================================================
# 7. VISUALISASI PETA RIIL LAPANGAN DIGITAL
# ==============================================================================
st.markdown("<br>", unsafe_allow_html=True)
st.subheader("🗺️ Peta Distribusi Geografis Jalur Konstruksi")

if len(st.session_state['titik_jaringan']) > 0:
    st.map(df_visual, latitude="lat", longitude="lon", color="color", size="size")
    st.caption("Keterangan Warna Titik Peta: 🔴 Titik Merah = ODP Utama | 🪵 Titik Abu-Abu = Tiang Tumpuan | 🏠 Titik Biru = Rumah Pelanggan.")
else:
    data_kosong = pd.DataFrame([{"lat": lat_sekarang, "lon": lon_sekarang, "color": "#00ff00", "size": 50}])
    st.map(data_kosong, latitude="lat", longitude="lon", color="color", size="size")