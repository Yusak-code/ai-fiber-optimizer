import streamlit as st
import networkx as nx
import folium
from streamlit_folium import st_folium
from streamlit_js_eval import streamlit_js_eval

# ==============================================================================
# 1. KONFIGURASI HALAMAN WEB (RESPONSIF UNTUK LAPTOP & HP)
# ==============================================================================
st.set_page_config(
    page_title="AI Drop Core Optimizer", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

st.title("⚡ AI-Based Drop Core Cable Route Optimizer (Live Geotagging)")
st.write("Sistem Cerdas Rekomendasi Jalur Kabel FTTH Berbasis Koordinat GPS Riil untuk PT DARIA PRATAMA MANDIRI.")
st.markdown("---")

# ==============================================================================
# 2. INISIALISASI DATA KORDINAT TIANG ODP RIIL (CONTOH WILAYAH PASURUAN)
# ==============================================================================
@st.cache_data
def inisialisasi_jaringan_riil():
    G = nx.Graph()
    
    # Koordinat GPS Asli Tiang ODP milik ISP (Contoh di sekitar Pasuruan)
    posisi_gps = {
        'ODP_Pusat_Daria': [-7.6405, 112.9010],
        'Tiang_A_Bawah': [-7.6415, 112.9025],
        'Tiang_C_Bawah': [-7.6425, 112.9040],
        'Tiang_B_Atas': [-7.6395, 112.9020],
        'Tiang_D_Atas': [-7.6390, 112.9038]
    }
    
    # Hubungkan antar tiang distribusi (Bobot dihitung dari perkiraan jarak geografis)
    G.add_edge('ODP_Pusat_Daria', 'Tiang_A_Bawah', jarak=45, belokan=1, hazard=False)
    G.add_edge('Tiang_A_Bawah', 'Tiang_C_Bawah', jarak=55, belokan=1, hazard=False)
    
    G.add_edge('ODP_Pusat_Daria', 'Tiang_B_Atas', jarak=35, belokan=2, hazard=False)
    G.add_edge('Tiang_B_Atas', 'Tiang_D_Atas', jarak=40, belokan=1, hazard=True) # Jalur rawan pohon rimbun
    
    return G, posisi_gps

G, posisi_gps = inisialisasi_jaringan_riil()

# ==============================================================================
# 3. PANEL KONTROL INPUT & LIVE GEOTAGGING GPS HP
# ==============================================================================
st.sidebar.header("📍 Fitur Survei Lapangan & GPS")

# Tombol untuk menangkap lokasi GPS asli dari smartphone teknisi
st.sidebar.write("Ambil Lokasi Rumah Pelanggan Secara Live:")
tombol_gps = st.sidebar.button("🎯 Ambil Koordinat GPS HP Saya", use_container_width=True)

# Variabel default koordinat rumah jika tombol GPS tidak diklik (sebagai fallback simulator)
lat_rumah = -7.6432
lon_rumah = 112.9055

if tombol_gps:
    # Memanggil API GPS Browser bawaan HP teknisi
    lokasi = streamlit_js_eval(data_of='geolocation', stop_after_once=True, want_to_see=False)
    if lokasi:
        lat_rumah = lokasi['coords']['latitude']
        lon_rumah = lokasi['coords']['longitude']
        st.sidebar.success(f"GPS Terkunci: {lat_rumah:.5f}, {lon_rumah:.5f}")
    else:
        st.sidebar.error("Gagal mendapatkan GPS. Pastikan izin lokasi browser Anda aktif.")

st.sidebar.markdown("---")
st.sidebar.subheader("🧠 Parameter Algoritma AI")

# Pilihan ODP Asal dan Hambatan
titik_awal = st.sidebar.selectbox("Pilih Titik ODP Asal:", ['ODP_Pusat_Daria'])
penalti_belokan = st.sidebar.slider("Faktor Penalti Belokan Kabel (dBm):", 0.0, 1.0, 0.5, step=0.1)
hindari_pohon = st.sidebar.checkbox("Hindari Jalur Pohon Rimbun (Jalur Atas)", value=True)

hitung_tombol = st.sidebar.button("ANALISIS JALUR TERBAIK 🤖", type="primary", use_container_width=True)

# ==============================================================================
# 4. PROSES ALGORITMA AI & PERHITUNGAN LOSS BUDGET
# ==============================================================================
if hitung_tombol:
    # Dinamis tambahkan titik Rumah Pelanggan hasil tagging ke dalam Graf Jaringan
    G.add_node('RUMAH_PELANGGAN')
    posisi_gps['RUMAH_PELANGGAN'] = [lat_rumah, lon_rumah]
    
    # Hubungkan Rumah Pelanggan ke tiang-tiang distribusi terdekat
    G.add_edge('Tiang_C_Bawah', 'RUMAH_PELANGGAN', jarak=30, belokan=1, hazard=False)
    G.add_edge('Tiang_D_Atas', 'RUMAH_PELANGGAN', jarak=25, belokan=2, hazard=False)

    # Kalkulasi pembobotan cerdas AI berdasarkan kondisi rintangan
    for u, v, data in G.edges(data=True):
        bobot_kalkulasi = data['jarak']
        bobot_kalkulasi += data['belokan'] * (penalti_belokan * 20)
        if hindari_pohon and data.get('hazard', False):
            bobot_kalkulasi += 1000  # Penalti besar agar AI mencari rute lain
        G[u][v]['bobot_ai'] = bobot_kalkulasi

    # AI Mengeksekusi pencarian rute terpendek yang paling aman
    rute_terbaik = nx.shortest_path(G, source=titik_awal, target='RUMAH_PELANGGAN', weight='bobot_ai')
    
    # Hitung Metrik Teknis Fisik Jalur Terpilih
    total_jarak = sum(G[rute_terbaik[i]][rute_terbaik[i+1]]['jarak'] for i in range(len(rute_terbaik)-1))
    total_belokan = sum(G[rute_terbaik[i]][rute_terbaik[i+1]]['belokan'] for i in range(len(rute_terbaik)-1))
    
    # Rumus Estimasi Redaman Riil Telekomunikasi FTTH
    loss_kabel = total_jarak * 0.0035 
    loss_konektor = 0.6               
    loss_bending = total_belokan * 0.1 
    total_redaman = -(19.0 + loss_kabel + loss_konektor + loss_bending)

    # Output Kesimpulan AI
    st.subheader("📋 Hasil Analisis Kecerdasan Buatan (AI)")
    nama_jalur = "Jalur Bawah (Aman dari Rintangan)" if 'Tiang_A_Bawah' in rute_terbaik else "Jalur Atas (Dekat Pohon)"
    st.success(f"🤖 **Rekomendasi Rute:** Menggunakan **{nama_jalur}** -> `{' ➡️ '.join(rute_terbaik)}`")
    
    # Tampilan Indikator Metrik (Scannable Cards)
    col1, col2, col3 = st.columns(3)
    col1.metric("Panjang Kabel Dipotong", f"{total_jarak} Meter")
    col2.metric("Jumlah Titik Belokan", f"{total_belokan} Sudut")
    
    if total_redaman >= -23.0:
        col3.metric("Estimasi Redaman Akhir", f"{total_redaman:.2f} dBm", delta="🟢 AMAN")
    elif -26.0 <= total_redaman < -23.0:
        col3.metric("Estimasi Redaman Akhir", f"{total_redaman:.2f} dBm", delta="🟡 WARNING", delta_color="inverse")
    else:
        col3.metric("Estimasi Redaman Akhir", f"{total_redaman:.2f} dBm", delta="🔴 CRITICAL / LOS", delta_color="inverse")

    # ==============================================================================
    # 5. INTEGRASI PETA SATELIT DIGITAL INTERAKTIF (FOLIUM/MAPS)
    # ==============================================================================
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("🗺️ Peta Digital Bentangan Kabel Jaringan (Riil)")
    
    # Buat peta dasar digital folium diarahkan ke posisi ODP Pusat
    peta = folium.Map(location=posisi_gps['ODP_Pusat_Daria'], zoom_start=17, control_scale=True)
    
    # Tambahkan marker penanda untuk setiap tiang infrastruktur
    for nama_tiang, koordinat in posisi_gps.items():
        if nama_tiang == 'ODP_Pusat_Daria':
            folium.Marker(koordinat, popup="ODP Utama Daria", icon=folium.Icon(color="red", icon="hdd")).add_to(peta)
        elif nama_tiang == 'RUMAH_PELANGGAN':
            folium.Marker(koordinat, popup="Hasil Tagging Rumah User", icon=folium.Icon(color="blue", icon="home")).add_to(peta)
        else:
            folium.Marker(koordinat, popup=f"Infrastruktur {nama_tiang}", icon=folium.Icon(color="gray", icon="info-sign")).add_to(peta)

    # Gambar rute kabel hijau tebal di atas peta jalan riil berdasarkan keputusan AI
    kordinat_rute_kabel = [posisi_gps[node] for node in rute_terbaik]
    folium.PolyLine(kordinat_rute_kabel, color="#2ecc71", weight=6, opacity=0.9, popup="Rute Kabel Pilihan AI").add_to(peta)
    
    # Render peta folium ke halaman web Streamlit
    st_folium(peta, width="100%", height=450)

else:
    st.warning("👈 Silakan atur parameter lapangan di panel menu kiri, lalu tekan tombol 'ANALISIS JALUR TERBAIK' untuk menyalakan peta satelit riil.")