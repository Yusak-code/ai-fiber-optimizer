import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt

# ==============================================================================
# 1. KONFIGURASI HALAMAN WEB (RESPONSIF UNTUK LAPTOP & HP)
# ==============================================================================
st.set_page_config(
    page_title="AI Drop Core Optimizer", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

st.title("⚡ AI-Based Drop Core Cable Route Optimizer")
st.write("Sistem Cerdas Rekomendasi & Perbandingan Jalur Penarikan Kabel FTTH untuk Meminimalkan Redaman.")
st.markdown("---")

# ==============================================================================
# 2. INISIALISASI GRAF JARINGAN (SIMULASI PETA UTAMA DENGAN MULTI-RUTE)
# ==============================================================================
@st.cache_data
def inisialisasi_jaringan():
    G = nx.Graph()
    
    # Koordinat Posisi Tiang/Rumah (X, Y dalam meter)
    posisi = {
        'ODP_Utama': (0, 3),
        'Tiang_A': (3, 1),   # Jalur Alternatif 1 (Bawah)
        'Tiang_C': (6, 2),
        'Tiang_B': (2, 6),   # Jalur Alternatif 2 (Atas)
        'Tiang_D': (5, 7),
        'RUMAH_PELANGGAN': (9, 4)
    }
    
    # Hubungkan antar titik beserta karakteristik fisik lapangannya
    # RUTE 1: Jalur Bawah (Lewat Tiang A dan C)
    G.add_edge('ODP_Utama', 'Tiang_A', jarak=30, belokan=1, hazard=False, label="Rute Bawah")
    G.add_edge('Tiang_A', 'Tiang_C', jarak=40, belokan=1, hazard=False, label="Rute Bawah")
    G.add_edge('Tiang_C', 'RUMAH_PELANGGAN', jarak=35, belokan=1, hazard=False, label="Rute Bawah")
    
    # RUTE 2: Jalur Atas (Lewat Tiang B dan D)
    G.add_edge('ODP_Utama', 'Tiang_B', jarak=25, belokan=2, hazard=False, label="Rute Atas")
    G.add_edge('Tiang_B', 'Tiang_D', jarak=30, belokan=1, hazard=True, label="Rute Atas") # Jalur rawan pohon
    G.add_edge('Tiang_D', 'RUMAH_PELANGGAN', jarak=20, belokan=1, hazard=False, label="Rute Atas")
    
    return G, posisi

G, posisi = inisialisasi_jaringan()

# ==============================================================================
# 3. PANEL KONTROL INPUT (MENU UTAMA SIDEBAR)
# ==============================================================================
st.sidebar.header("📍 Parameter Survei Lapangan")

# Pilihan Titik Awal dan Akhir
titik_awal = st.sidebar.selectbox("Pilih Tiang ODP Asal:", ['ODP_Utama'])
titik_tujuan = st.sidebar.selectbox("Pilih Tujuan Rumah:", ['RUMAH_PELANGGAN'])

st.sidebar.markdown("---")
st.sidebar.subheader("🧠 Parameter Algoritma AI")

# Slider untuk mengatur sensitivitas penalti belokan kabel
penalti_belokan = st.sidebar.slider("Faktor Penalti Belokan Kabel (dBm/Sudut):", 0.0, 1.0, 0.5, step=0.1)

# Fitur deteksi rintangan dinamis oleh teknisi
st.sidebar.write("Kondisi Rintangan di Lokasi:")
hindari_pohon = st.sidebar.checkbox("Hindari Jalur Pohon Rimbun (Jalur Atas)", value=True)

# Tombol Utama Eksekusi AI
st.sidebar.markdown("<br>", unsafe_allow_html=True)
hitung_tombol = st.sidebar.button("ANALISIS & CARI RUTE OPTIMAL 🤖", type="primary", use_container_width=True)

# ==============================================================================
# 4. PROSES ALGORITMA AI OPTIMASI & PERBANDINGAN RUTE
# ==============================================================================
if hitung_tombol:
    # --- PROSES EVALUASI MULTI-RUTE SECARA DIGITAL OLEH AI ---
    
    # Fungsi pembantu untuk menghitung parameter rute spesifik
    def kalkulasi_metrik_jalur(jalur_nodes):
        jarak = sum(G[jalur_nodes[i]][jalur_nodes[i+1]]['jarak'] for i in range(len(jalur_nodes)-1))
        belokan = sum(G[jalur_nodes[i]][jalur_nodes[i+1]]['belokan'] for i in range(len(jalur_nodes)-1))
        loss_kabel = jarak * 0.0035 
        loss_konektor = 0.6               
        loss_bending = belokan * 0.1 
        redaman = -(19.0 + loss_kabel + loss_konektor + loss_bending)
        return jarak, belokan, redaman

    # Definisikan 2 rute alternatif yang tersedia di lapangan secara manual untuk perbandingan
    rute_alternatif_1 = ['ODP_Utama', 'Tiang_A', 'Tiang_C', 'RUMAH_PELANGGAN'] # Rute Bawah
    rute_alternatif_2 = ['ODP_Utama', 'Tiang_B', 'Tiang_D', 'RUMAH_PELANGGAN'] # Rute Atas
    
    j1, b1, r1 = kalkulasi_metrik_jalur(rute_alternatif_1)
    j2, b2, r2 = kalkulasi_metrik_jalur(rute_alternatif_2)

    # Terapkan penalti dinamis ke dalam Graf untuk diproses oleh Algoritma Pencarian Lintasan Terpendek (Dijkstra)
    for u, v, data in G.edges(data=True):
        bobot_kalkulasi = data['jarak']  
        bobot_kalkulasi += data['belokan'] * (penalti_belokan * 20)
        
        # Jika teknisi mencentang hindari pohon, jalur atas diberikan penalti beban yang sangat besar
        if hindari_pohon and data['hazard']:
            bobot_kalkulasi += 1000  
            
        G[u][v]['bobot_ai'] = bobot_kalkulasi

    # AI mengeksekusi keputusan akhir rute terbaik
    rute_terbaik = nx.shortest_path(G, source=titik_awal, target=titik_tujuan, weight='bobot_ai')
    jarak_terpilih, belokan_terpilih, redaman_terpilih = kalkulasi_metrik_jalur(rute_terbaik)

    # --- TAMPILAN OUTPUT UTAMA ---
    st.subheader("📋 Hasil Analisis Kecerdasan Buatan (AI)")
    
    # Kotak informasi kesimpulan rute
    nama_rute_pilihan = "RUTE BAWAH (Aman)" if 'Tiang_A' in rute_terbaik else "RUTE ATAS (Dekat Pohon)"
    st.success(f"🤖 *Keputusan AI:* Direkomendasikan menggunakan *{nama_rute_pilihan}* dengan rute jalur: {' ➡️ '.join(rute_terbaik)}")
    
    # Widget Tampilan Metrik Rute Terpilih
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Panjang Kabel Dibutuhkan", value=f"{jarak_terpilih} Meter")
    with col2:
        st.metric(label="Jumlah Sudut Tikungan", value=f"{belokan_terpilih} Titik")
    with col3:
        if redaman_terpilih >= -23.0:
            st.metric(label="Estimasi Redaman Sinyal", value=f"{redaman_terpilih:.2f} dBm", delta="🟢 AMAN")
        elif -26.0 <= redaman_terpilih < -23.0:
            st.metric(label="Estimasi Redaman Sinyal", value=f"{redaman_terpilih:.2f} dBm", delta="🟡 WARNING", delta_color="inverse")
        else:
            st.metric(label="Estimasi Redaman Sinyal", value=f"{redaman_terpilih:.2f} dBm", delta="🔴 CRITICAL / LOS", delta_color="inverse")

    # --- TABEL PERBANDINGAN MULTI-RUTE (DASHBOARD MANAJEMEN) ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("⚖️ Tabel Perbandingan Semua Rute Alternatif")
    st.write("Analisis komparatif digital tanpa perlu melakukan survei fisik berulang kali:")
    
    # Buat tabel perbandingan sederhana
    st.markdown(f"""

    | Rute Alternatif | Total Jarak Fisik | Total Belokan | Perkiraan Redaman | Status Rintangan Lapangan | Keputusan AI |
    | :--- | :---: | :---: | :---: | :--- | :---: |
    | *Jalur Bawah (Lewat Tiang A & C)* | {j1} Meter | {b1} Titik | {r1:.2f} dBm | Bersih dari hambatan | {'✅ DIPILIH (Paling Aman)' if rute_terbaik == rute_alternatif_1 else '❌ Ditolak'} |
    | *Jalur Atas (Lewat Tiang B & D)* | {j2} Meter | {b2} Titik | {r2:.2f} dBm | { '⚠️ Rawan Pohon Tumbang' if hindari_pohon else 'Diabaikan' } | {'✅ DIPILIH (Jarak Terpendek)' if rute_terbaik == rute_alternatif_2 else '❌ Ditolak (Beresiko)'} |
    """)

    # ==============================================================================
    # 5. VISUALISASI INTEGRASI PETA GRAFIK JARINGAN
    # ==============================================================================
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📊 Visualisasi Peta Penarikan Kabel")
    fig, ax = plt.subplots(figsize=(12, 5))
    
    # Gambar Titik Tiang & Rumah
    nx.draw_networkx_nodes(G, posisi, node_color='#b2bec3', node_size=700, ax=ax)
    nx.draw_networkx_labels(G, posisi, font_size=9, font_weight='bold', font_color='#2d3436', ax=ax)
    
    # Gambar Semua Alternatif Jalur Kabel (Garis Tipis Abu-abu)
    nx.draw_networkx_edges(G, posisi, edgelist=G.edges(), edge_color='#dfe6e9', width=2, ax=ax)
    
    # Warnai Jalur Pilihan AI (Garis Tebal Hijau Semanggi)
    jalur_terpilih_edges = [(rute_terbaik[i], rute_terbaik[i+1]) for i in range(len(rute_terbaik)-1)]
    nx.draw_networkx_edges(G, posisi, edgelist=jalur_terpilih_edges, edge_color='#2ecc71', width=6, ax=ax)
    
    # Konfigurasi Tampilan Grafik
    ax.set_xlim(-1, 11)
    ax.set_ylim(0, 9)
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.xlabel("Grid Wilayah Horisontal (Meter)")
    plt.ylabel("Grid Wilayah Vertikal (Meter)")
    
    st.pyplot(fig)

else:
    # Tampilan Awal UI/UX Responsif sebelum tombol diklik
    st.warning("👈 Silakan atur parameter kondisi lapangan di menu sebelah kiri (atau klik ikon menu hamburger ☰ di pojok kiri atas jika Anda membuka lewat HP), lalu klik tombol 'ANALISIS & CARI RUTE OPTIMAL' untuk memproses simulasi.")