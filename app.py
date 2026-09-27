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
# 2. PANEL KONTROL INPUT & LIVE GEOTAGGING GPS HP (VERSI AMAN & STABIL)
# ==============================================================================
@st.fragment
def render_sidebar_gps():
    st.sidebar.header("📍 Fitur Survei Lapangan & GPS")
    st.sidebar.write("Ambil Lokasi Rumah Pelanggan Secara Live:")
    
    st.sidebar.button("🔄 Panggil & Kunci Sinyal GPS", use_container_width=True)
    
    lokasi_gps = streamlit_js_eval(
        js_expressions="new Promise((resolve) => { navigator.geolocation.getCurrentPosition((pos) => { resolve([pos.coords.latitude, pos.coords.longitude]) }, (err) => { resolve(null) }, { enableHighAccuracy: true, timeout: 6000 }) })", 
        want_output=True, 
        key="get_user_gps_final"
    )
    
    # Nilai default konstan agar aplikasi TIDAK BISA CRASH meskipun GPS HP mati
    lat = -7.6432
    lon = 112.9055
    
    if lokasi_gps and isinstance(lokasi_gps, list) and len(lokasi_gps) == 2:
        if lokasi_gps[0] is not None and lokasi_gps[1] is not None:
            lat = float(lokasi_gps[0])
            lon = float(lokasi_gps[1])
            st.sidebar.success(f"🟢 GPS Terkunci: {lat:.5f}, {lon:.5f}")
        else:
            st.sidebar.warning("📡 Menggunakan Mode Simulasi (GPS Browser Belum Siap).")
    else:
        st.sidebar.warning("📡 Menggunakan Mode Simulasi (GPS Browser Belum Siap).")
        
    return lat, lon

# Menangkap koordinat secara aman
lat_rumah, lon_rumah = render_sidebar_gps()

# ==============================================================================
# 3. DYNAMIC GENERATOR TIANG ODP (ANTI-CRASH)
# ==============================================================================
def inisialisasi_jaringan_riil(lat_user, lon_user):
    G = nx.Graph()
    
    # Menghasilkan letak tiang secara dinamis di sekitar lokasi user secara presisi
    posisi_gps = {
        'ODP_Pusat_Daria': [lat_user + 0.002, lon_user - 0.002],
        'Tiang_A_Bawah': [lat_user + 0.001, lon_user - 0.001],
        'Tiang_C_Bawah': [lat_user + 0.0005, lon_user - 0.0005],
        'Tiang_B_Atas': [lat_user + 0.0015, lon_user - 0.001],
        'Tiang_D_Atas': [lat_user + 0.0008, lon_user - 0.0003]
    }
    
    G.add_edge('ODP_Pusat_Daria', 'Tiang_A_Bawah', jarak=45, belokan=1, hazard=False)
    G.add_edge('Tiang_A_Bawah', 'Tiang_C_Bawah', jarak=55, belokan=1, hazard=False)
    G.add_edge('ODP_Pusat_Daria', 'Tiang_B_Atas', jarak=35, belokan=2, hazard=False)
    G.add_edge('Tiang_B_Atas', 'Tiang_D_Atas', jarak=40, belokan=1, hazard=True) 
    
    return G, posisi_gps

G, posisi_gps = inisialisasi_jaringan_riil(lat_rumah, lon_rumah)

# Parameter menu kontrol di bagian bawah GPS
st.sidebar.markdown("---")
st.sidebar.subheader("🧠 Parameter Algoritma AI")

titik_awal = st.sidebar.selectbox("Pilih Titik ODP Asal:", ['ODP_Pusat_Daria'])
penalti_belokan = st.sidebar.slider("Faktor Penalti Belokan Kabel (dBm):", 0.0, 1.0, 0.5, step=0.1)
hindari_pohon = st.sidebar.checkbox("Hindari Jalur Pohon Rimbun (Jalur Atas)", value=True)

hitung_tombol = st.sidebar.button("ANALISIS JALUR TERBAIK 🤖", type="primary", use_container_width=True)

# ==============================================================================
# 4. PROSES ALGORITMA AI & PERHITUNGAN LOSS BUDGET
# ==============================================================================
if hitung_tombol:
    # Daftarkan Rumah Pelanggan ke struktur peta AI menggunakan GPS dinamis
    G.add_node('RUMAH_PELANGGAN')
    posisi_gps['RUMAH_PELANGGAN'] = [lat_rumah, lon_rumah]
    
    # Menghubungkan Rumah Pelanggan ke Tiang_C dan Tiang_D secara dinamis
    G.add_edge('Tiang_C_Bawah', 'RUMAH_PELANGGAN', jarak=30, belokan=1, hazard=False)
    G.add_edge('Tiang_D_Atas', 'RUMAH_PELANGGAN', jarak=25, belokan=2, hazard=False)

    # Kalkulasi pembobotan cerdas AI berdasarkan kondisi rintangan
    for u, v, data in G.edges(data=True):
        bobot_kalkulasi = data['jarak']
        bobot_kalkulasi += data['belokan'] * (penalti_belokan * 20)
        if hindari_pohon and data.get('hazard', False):
            bobot_kalkulasi += 1000  
        G[u][v]['bobot_ai'] = bobot_kalkulasi

    try:
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
        
        # Buat peta dasar digital folium diarahkan ke posisi User saat ini
        peta = folium.Map(location=[lat_rumah, lon_rumah], zoom_start=17, control_scale=True)
        
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
        
    except Exception as e:
        st.error(f"Terjadi kesalahan kalkulasi rute rintangan: {e}")

else:
    st.warning("👈 Silakan atur parameter lapangan di panel menu kiri, lalu tekan tombol 'ANALISIS JALUR TERBAIK' untuk menyalakan peta satelit riil.")