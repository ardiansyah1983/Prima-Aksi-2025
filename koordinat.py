import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import plotly.express as px
import numpy as np
import math
import os
import glob

# Fungsi untuk menghitung jarak antara dua koordinat (tanpa geopy)
def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Menghitung jarak antara dua titik koordinat menggunakan rumus Haversine
    Hasil dalam meter
    """
    # Konversi derajat ke radian
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Rumus Haversine
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius bumi dalam meter
    r = 6371000
    
    return c * r

# Konfigurasi halaman
st.set_page_config(
    page_title="Peta Interaktif - Auto Load CSV",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS untuk styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-container {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .filter-section {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .file-info {
        background-color: #e8f4fd;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Header utama
st.markdown('<div class="main-header">🗺️ Peta Interaktif Spektrum Frekuensi Radio</div>', unsafe_allow_html=True)
st.markdown('<div style="text-align: center; color: #666; margin-bottom: 2rem;">Auto Load CSV dari Folder Data</div>', unsafe_allow_html=True)

# Fungsi untuk mencari file CSV di folder Data
@st.cache_data
def get_csv_files():
    """Mencari semua file CSV di folder Data"""
    data_folder = "Data"
    csv_files = []
    
    # Cek apakah folder Data ada
    if os.path.exists(data_folder):
        # Cari semua file CSV di folder Data
        csv_pattern = os.path.join(data_folder, "*.csv")
        csv_files = glob.glob(csv_pattern)
        # Ambil hanya nama file, bukan path lengkap
        csv_files = [os.path.basename(file) for file in csv_files]
    
    return csv_files

# Fungsi untuk load data dengan error handling yang lebih baik
@st.cache_data
def load_data(selected_file):
    """Load dan preprocess data CSV dari folder Data"""
    if not selected_file:
        return pd.DataFrame(), "Tidak ada file yang dipilih"
    
    try:
        file_path = os.path.join("Data", selected_file)
        
        # Baca file CSV dengan berbagai encoding
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        df = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if df is None:
            return pd.DataFrame(), "Error: Tidak dapat membaca file dengan encoding yang tersedia"
        
        # Cek kolom yang diperlukan
        required_coords = ['SID_LONG', 'SID_LAT']
        missing_coords = [col for col in required_coords if col not in df.columns]
        
        if missing_coords:
            return pd.DataFrame(), f"Error: Kolom koordinat tidak ditemukan: {missing_coords}"
        
        # Clean data - hapus baris dengan koordinat kosong
        original_rows = len(df)
        df = df.dropna(subset=['SID_LONG', 'SID_LAT'])
        
        # Pastikan koordinat adalah numerik
        df['SID_LONG'] = pd.to_numeric(df['SID_LONG'], errors='coerce')
        df['SID_LAT'] = pd.to_numeric(df['SID_LAT'], errors='coerce')
        
        # Pastikan kolom opsional juga numerik (jika ada)
        optional_coords = ['LONGITUDE_CENTER_KALKULASI', 'LATITUDE_CENTER_KALKULASI']
        for col in optional_coords:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Hapus baris dengan koordinat invalid
        df = df.dropna(subset=['SID_LONG', 'SID_LAT'])
        cleaned_rows = len(df)
        
        success_message = f"Berhasil load {cleaned_rows} dari {original_rows} baris data"
        return df, success_message
        
    except Exception as e:
        return pd.DataFrame(), f"Error loading data: {str(e)}"

# Sidebar untuk pemilihan file dan kontrol
st.sidebar.markdown("## 📁 Pilih File CSV")

# Cari file CSV di folder Data
csv_files = get_csv_files()

if not csv_files:
    st.sidebar.error("❌ Folder 'Data' tidak ditemukan atau tidak ada file CSV")
    st.error("""
    **Folder 'Data' tidak ditemukan!**
    
    Silakan:
    1. Buat folder bernama 'Data' di direktori yang sama dengan aplikasi ini
    2. Letakkan file CSV Anda di dalam folder 'Data'
    3. Refresh aplikasi ini
    
    Struktur folder yang diharapkan:
    ```
    your_app_folder/
    ├── app.py (file aplikasi ini)
    ├── Data/
    │   ├── file1.csv
    │   ├── file2.csv
    │   └── ...
    ```
    """)
    st.stop()

# Dropdown untuk memilih file CSV
selected_file = st.sidebar.selectbox(
    "Pilih file CSV:",
    options=[""] + csv_files,
    index=0,
    help="Pilih file CSV dari folder Data yang ingin divisualisasikan"
)

if not selected_file:
    st.info("👆 Silakan pilih file CSV dari sidebar untuk memulai")
    st.stop()

# Load data
df, load_message = load_data(selected_file)

# Tampilkan informasi file
st.markdown(f"""
<div class="file-info">
    <h4>📄 File yang dipilih: {selected_file}</h4>
    <p><strong>Status:</strong> {load_message}</p>
</div>
""", unsafe_allow_html=True)

if df.empty:
    st.error(f"Tidak dapat memuat data: {load_message}")
    st.stop()

# Tampilkan informasi kolom yang tersedia
st.sidebar.markdown("### 📋 Info Data")

# Hitung statistik toleransi jika ada koordinat center
tolerance_info = ""
if ('LATITUDE_CENTER_KALKULASI' in df.columns and 
    'LONGITUDE_CENTER_KALKULASI' in df.columns):
    
    # Hitung data yang melebihi toleransi untuk info
    exceed_count = 0
    total_valid = 0
    
    for idx, row in df.iterrows():
        if (pd.notna(row['SID_LAT']) and pd.notna(row['SID_LONG']) and 
            pd.notna(row['LATITUDE_CENTER_KALKULASI']) and pd.notna(row['LONGITUDE_CENTER_KALKULASI'])):
            
            distance = calculate_distance(
                row['SID_LAT'], row['SID_LONG'],
                row['LATITUDE_CENTER_KALKULASI'], row['LONGITUDE_CENTER_KALKULASI']
            )
            total_valid += 1
            if distance > 20:
                exceed_count += 1
    
    tolerance_info = f"\n**Toleransi 20m:** {exceed_count}/{total_valid} melebihi"

st.sidebar.info(f"""
**Total Baris:** {len(df)}
**Total Kolom:** {len(df.columns)}
**Koordinat:** ✅ SID_LONG, SID_LAT{tolerance_info}
""")

# Cek dan tampilkan kolom yang tersedia untuk filter
available_filter_columns = {
    'CLNT_NAME': 'CLNT_NAME' in df.columns,
    'STATUS_MYSPECTRA': 'STATUS_MYSPECTRA' in df.columns,
    'CITY': 'CITY' in df.columns,
    'Status Verifikasi UPT 2024': 'Status Verifikasi UPT 2024' in df.columns,
    'Center Coordinates': ('LATITUDE_CENTER_KALKULASI' in df.columns and 
                          'LONGITUDE_CENTER_KALKULASI' in df.columns)
}

st.sidebar.markdown("**Filter Tersedia:**")
for col, available in available_filter_columns.items():
    st.sidebar.write(f"{'✅' if available else '❌'} {col}")

# Sidebar untuk filter dan kontrol
st.sidebar.markdown("## 🔧 Kontrol Peta")

# Filter berdasarkan kolom yang tersedia
st.sidebar.markdown("### 📊 Filter Data")

# Filter CLNT_NAME (jika ada)
selected_clnt = "Semua"
if 'CLNT_NAME' in df.columns:
    clnt_names = ['Semua'] + sorted(df['CLNT_NAME'].dropna().unique().tolist())
    selected_clnt = st.sidebar.selectbox("Pilih Client Name:", clnt_names)

# Filter STATUS_MYSPECTRA (jika ada)
selected_status = "Semua"
if 'STATUS_MYSPECTRA' in df.columns:
    status_myspectra = ['Semua'] + sorted(df['STATUS_MYSPECTRA'].dropna().unique().tolist())
    selected_status = st.sidebar.selectbox("Pilih Status MySpectra:", status_myspectra)

# Filter CITY (jika ada)
selected_city = "Semua"
if 'CITY' in df.columns:
    cities = ['Semua'] + sorted(df['CITY'].dropna().unique().tolist())
    selected_city = st.sidebar.selectbox("Pilih Kota:", cities)

# Filter Status Verifikasi UPT 2024 (jika ada)
selected_verification = "Semua"
if 'Status Verifikasi UPT 2024' in df.columns:
    verification_status = ['Semua'] + sorted(df['Status Verifikasi UPT 2024'].dropna().unique().tolist())
    selected_verification = st.sidebar.selectbox("Pilih Status Verifikasi UPT 2024:", verification_status)

# Pilihan koordinat untuk perbandingan
st.sidebar.markdown("### 📍 Perbandingan Koordinat")
coord_options = ["SID (SID_LONG, SID_LAT)"]

# Tambahkan opsi center jika kolom tersedia
if 'LONGITUDE_CENTER_KALKULASI' in df.columns and 'LATITUDE_CENTER_KALKULASI' in df.columns:
    coord_options.extend([
        "Center (LONGITUDE_CENTER_KALKULASI, LATITUDE_CENTER_KALKULASI)", 
        "Keduanya"
    ])

coord_option = st.sidebar.radio("Pilih set koordinat:", coord_options)

# Pilihan model peta
st.sidebar.markdown("### 🗺️ Model Peta")
map_style = st.sidebar.selectbox(
    "Pilih style peta:",
    ["OpenStreetMap", "Satellite", "Terrain", "CartoDB Positron", "CartoDB Dark_Matter"]
)

# Analisis Toleransi Toggle
st.sidebar.markdown("### 🔍 Analisis Koordinat")
show_tolerance_analysis = st.sidebar.checkbox(
    "Tampilkan Analisis Toleransi 20m", 
    value=True,
    help="Menampilkan analisis perbandingan koordinat dengan toleransi 20 meter"
)

# Filter berdasarkan toleransi (jika ada koordinat center)
tolerance_filter = "Semua"
if ('LATITUDE_CENTER_KALKULASI' in df.columns and 
    'LONGITUDE_CENTER_KALKULASI' in df.columns):
    tolerance_filter = st.sidebar.selectbox(
        "Filter Toleransi Koordinat:",
        ["Semua", "Hanya Melebihi 20m", "Hanya Dalam Toleransi 20m"],
        help="Filter data berdasarkan perbedaan koordinat SID dan Center"
    )

# Apply filters
filtered_df = df.copy()

if 'CLNT_NAME' in df.columns and selected_clnt != 'Semua':
    filtered_df = filtered_df[filtered_df['CLNT_NAME'] == selected_clnt]

if 'STATUS_MYSPECTRA' in df.columns and selected_status != 'Semua':
    filtered_df = filtered_df[filtered_df['STATUS_MYSPECTRA'] == selected_status]

if 'CITY' in df.columns and selected_city != 'Semua':
    filtered_df = filtered_df[filtered_df['CITY'] == selected_city]

if 'Status Verifikasi UPT 2024' in df.columns and selected_verification != 'Semua':
    filtered_df = filtered_df[filtered_df['Status Verifikasi UPT 2024'] == selected_verification]

# Filter berdasarkan toleransi koordinat
if (tolerance_filter != "Semua" and 
    'LATITUDE_CENTER_KALKULASI' in df.columns and 
    'LONGITUDE_CENTER_KALKULASI' in df.columns):
    
    # Hitung jarak untuk setiap baris
    tolerance_mask = []
    for idx, row in filtered_df.iterrows():
        if (pd.notna(row['SID_LAT']) and pd.notna(row['SID_LONG']) and 
            pd.notna(row['LATITUDE_CENTER_KALKULASI']) and pd.notna(row['LONGITUDE_CENTER_KALKULASI'])):
            
            distance = calculate_distance(
                row['SID_LAT'], row['SID_LONG'],
                row['LATITUDE_CENTER_KALKULASI'], row['LONGITUDE_CENTER_KALKULASI']
            )
            
            if tolerance_filter == "Hanya Melebihi 20m":
                tolerance_mask.append(distance > 20)
            elif tolerance_filter == "Hanya Dalam Toleransi 20m":
                tolerance_mask.append(distance <= 20)
        else:
            # Jika tidak ada data koordinat center, tidak masuk filter
            tolerance_mask.append(False)
    
    if tolerance_mask:
        filtered_df = filtered_df[tolerance_mask]

# Metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f'<div class="metric-container"><h3>{len(filtered_df)}</h3><p>Total Data Points</p></div>', unsafe_allow_html=True)

with col2:
    if 'CLNT_NAME' in df.columns:
        unique_clients = filtered_df['CLNT_NAME'].nunique()
        st.markdown(f'<div class="metric-container"><h3>{unique_clients}</h3><p>Unique Clients</p></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="metric-container"><h3>-</h3><p>Client Info</p></div>', unsafe_allow_html=True)

with col3:
    if 'CITY' in df.columns:
        unique_cities = filtered_df['CITY'].nunique()
        st.markdown(f'<div class="metric-container"><h3>{unique_cities}</h3><p>Cities</p></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="metric-container"><h3>-</h3><p>City Info</p></div>', unsafe_allow_html=True)

with col4:
    if 'STATUS_SIMF' in df.columns:
        granted_count = len(filtered_df[filtered_df['STATUS_SIMF'] == 'Granted'])
        st.markdown(f'<div class="metric-container"><h3>{granted_count}</h3><p>Granted Status</p></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="metric-container"><h3>-</h3><p>Status Info</p></div>', unsafe_allow_html=True)

# Fungsi untuk membuat peta
def create_map(data, coord_type, map_style):
    if data.empty:
        return None
        
    # Tentukan center peta berdasarkan data
    center_lat = data['SID_LAT'].mean()
    center_lon = data['SID_LONG'].mean()
    
    # Mapping style peta
    tile_options = {
        "OpenStreetMap": None,
        "Satellite": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "Terrain": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer/tile/{z}/{y}/{x}",
        "CartoDB Positron": "CartoDB positron",
        "CartoDB Dark_Matter": "CartoDB dark_matter"
    }
    
    # Buat peta dasar
    if map_style == "OpenStreetMap":
        m = folium.Map(location=[center_lat, center_lon], zoom_start=10)
    elif map_style in ["CartoDB Positron", "CartoDB Dark_Matter"]:
        m = folium.Map(location=[center_lat, center_lon], zoom_start=10, tiles=tile_options[map_style])
    else:
        m = folium.Map(location=[center_lat, center_lon], zoom_start=10)
        folium.TileLayer(
            tiles=tile_options[map_style],
            attr=map_style,
            name=map_style
        ).add_to(m)
    
    # Color mapping untuk client names (jika ada kolom CLNT_NAME)
    if 'CLNT_NAME' in data.columns:
        unique_clients = data['CLNT_NAME'].unique()
        colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 
                  'beige', 'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 'white', 
                  'pink', 'lightblue', 'lightgreen', 'gray', 'black', 'lightgray']
        color_map = {client: colors[i % len(colors)] for i, client in enumerate(unique_clients)}
    else:
        color_map = {}
    
    # Tambahkan markers berdasarkan pilihan koordinat
    for idx, row in data.iterrows():
        # Buat popup content dinamis berdasarkan kolom yang tersedia
        popup_content = "<div style='width: 300px;'>"
        
        # Header dengan nama stasiun (jika ada)
        if 'STN_NAME' in row and pd.notna(row['STN_NAME']):
            popup_content += f"<h4><b>{row['STN_NAME']}</b></h4><hr>"
        else:
            popup_content += f"<h4><b>Data Point #{idx}</b></h4><hr>"
        
        # Informasi dinamis berdasarkan kolom yang tersedia
        info_fields = {
            'CLNT_NAME': 'Client',
            'CITY': 'Kota',
            'STATUS_MYSPECTRA': 'Status MySpectra',
            'Status Verifikasi UPT 2024': 'Status Verifikasi UPT',
            'FREQ': 'Frequency (MHz)',
            'ERP_PWR_DBM': 'Power (dBm)',
            'STN_ADDR': 'Alamat'
        }
        
        for col, label in info_fields.items():
            if col in row and pd.notna(row[col]):
                value = row[col]
                if col in ['FREQ', 'ERP_PWR_DBM']:
                    popup_content += f"<b>{label}:</b> {value}<br>"
                else:
                    popup_content += f"<b>{label}:</b> {value}<br>"
        
        # Koordinat
        popup_content += "<hr><b>Koordinat SID:</b><br>"
        popup_content += f"Lat: {row['SID_LAT']}, Long: {row['SID_LONG']}<br>"
        
        if 'LATITUDE_CENTER_KALKULASI' in row and pd.notna(row['LATITUDE_CENTER_KALKULASI']):
            popup_content += "<b>Koordinat Center:</b><br>"
            popup_content += f"Lat: {row['LATITUDE_CENTER_KALKULASI']}, Long: {row['LONGITUDE_CENTER_KALKULASI']}"
        
        popup_content += "</div>"
        
        # Tentukan warna marker
        if 'CLNT_NAME' in row and row['CLNT_NAME'] in color_map:
            client_color = color_map[row['CLNT_NAME']]
        else:
            client_color = 'red'
        
        # Tentukan tooltip
        if 'STN_NAME' in row and pd.notna(row['STN_NAME']):
            if 'CLNT_NAME' in row and pd.notna(row['CLNT_NAME']):
                tooltip_text = f"{row['STN_NAME']} - {row['CLNT_NAME']}"
            else:
                tooltip_text = str(row['STN_NAME'])
        else:
            tooltip_text = f"Data Point #{idx}"
        
        # Add markers berdasarkan koordinat
        if coord_type == "SID (SID_LONG, SID_LAT)":
            folium.Marker(
                location=[row['SID_LAT'], row['SID_LONG']],
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=tooltip_text,
                icon=folium.Icon(color=client_color, icon='info-sign')
            ).add_to(m)
            
        elif coord_type.startswith("Center") and 'LATITUDE_CENTER_KALKULASI' in row:
            if pd.notna(row['LATITUDE_CENTER_KALKULASI']) and pd.notna(row['LONGITUDE_CENTER_KALKULASI']):
                folium.Marker(
                    location=[row['LATITUDE_CENTER_KALKULASI'], row['LONGITUDE_CENTER_KALKULASI']],
                    popup=folium.Popup(popup_content, max_width=300),
                    tooltip=f"{tooltip_text} (Center)",
                    icon=folium.Icon(color=client_color, icon='bullseye')
                ).add_to(m)
                
        elif coord_type == "Keduanya":
            # Marker untuk SID
            folium.Marker(
                location=[row['SID_LAT'], row['SID_LONG']],
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=f"{tooltip_text} - SID",
                icon=folium.Icon(color=client_color, icon='info-sign')
            ).add_to(m)
            
            # Marker untuk Center (jika ada)
            if (pd.notna(row.get('LATITUDE_CENTER_KALKULASI')) and 
                pd.notna(row.get('LONGITUDE_CENTER_KALKULASI'))):
                folium.Marker(
                    location=[row['LATITUDE_CENTER_KALKULASI'], row['LONGITUDE_CENTER_KALKULASI']],
                    popup=folium.Popup(popup_content, max_width=300),
                    tooltip=f"{tooltip_text} - Center",
                    icon=folium.Icon(color=client_color, icon='bullseye')
                ).add_to(m)
                
                # Garis penghubung antara SID dan Center
                folium.PolyLine(
                    locations=[[row['SID_LAT'], row['SID_LONG']], 
                              [row['LATITUDE_CENTER_KALKULASI'], row['LONGITUDE_CENTER_KALKULASI']]],
                    color=client_color,
                    weight=2,
                    opacity=0.7,
                    dash_array="5, 5"
                ).add_to(m)
    
    # Tambahkan legend jika ada data client
    if color_map:
        legend_html = '''
        <div style="position: fixed; 
                    top: 10px; right: 10px; width: 200px; height: auto; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <h4>Legend</h4>
        '''
        
        for client, color in list(color_map.items())[:10]:  # Batasi maksimal 10 legend
            legend_html += f'<p><i class="fa fa-circle" style="color:{color}"></i> {client[:25]}{"..." if len(client) > 25 else ""}</p>'
        
        if len(color_map) > 10:
            legend_html += f'<p><i>... dan {len(color_map) - 10} lainnya</i></p>'
        
        legend_html += '</div>'
        m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

# Main content area
col_left, col_right = st.columns([3, 1])

with col_left:
    st.markdown("### 🗺️ Peta Interaktif")
    
    if not filtered_df.empty:
        # Buat dan tampilkan peta
        map_obj = create_map(filtered_df, coord_option, map_style)
        if map_obj:
            map_data = st_folium(map_obj, width=800, height=600)
    else:
        st.warning("Tidak ada data yang sesuai dengan filter yang dipilih.")

with col_right:
    st.markdown("### 📈 Statistik")
    
    if not filtered_df.empty:
        # Chart distribusi client (jika kolom tersedia)
        if 'CLNT_NAME' in filtered_df.columns:
            fig_client = px.pie(
                filtered_df, 
                names='CLNT_NAME', 
                title='Distribusi Client',
                height=300
            )
            fig_client.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_client, use_container_width=True)
        
        # Chart distribusi kota (jika kolom tersedia)
        if 'CITY' in filtered_df.columns:
            city_counts = filtered_df['CITY'].value_counts().head(10)
            fig_city = px.bar(
                x=city_counts.values,
                y=city_counts.index,
                orientation='h',
                title='Top 10 Kota',
                height=300
            )
            fig_city.update_layout(yaxis_title="Kota", xaxis_title="Jumlah")
            st.plotly_chart(fig_city, use_container_width=True)

# Analisis Perbandingan Koordinat (jika ada koordinat center dan toggle aktif)
if (show_tolerance_analysis and 
    'LATITUDE_CENTER_KALKULASI' in filtered_df.columns and 
    'LONGITUDE_CENTER_KALKULASI' in filtered_df.columns):
    st.markdown("### 📊 Analisis Perbandingan Koordinat")
    
    # Hitung jarak antara SID dan Center coordinates
    distances = []
    valid_comparison = 0
    tolerance_exceeded = []
    coord_analysis_data = []
    
    for idx, row in filtered_df.iterrows():
        if (pd.notna(row['SID_LAT']) and pd.notna(row['SID_LONG']) and 
            pd.notna(row['LATITUDE_CENTER_KALKULASI']) and pd.notna(row['LONGITUDE_CENTER_KALKULASI'])):
            
            distance = calculate_distance(
                row['SID_LAT'], row['SID_LONG'],
                row['LATITUDE_CENTER_KALKULASI'], row['LONGITUDE_CENTER_KALKULASI']
            )
            distances.append(distance)
            valid_comparison += 1
            
            # Cek toleransi >20 meter
            if distance > 20:
                tolerance_exceeded.append({
                    'Index': idx,
                    'STN_NAME': row.get('STN_NAME', f'Data #{idx}'),
                    'CLNT_NAME': row.get('CLNT_NAME', 'N/A'),
                    'CITY': row.get('CITY', 'N/A'),
                    'SID_LAT': row['SID_LAT'],
                    'SID_LONG': row['SID_LONG'],
                    'CENTER_LAT': row['LATITUDE_CENTER_KALKULASI'],
                    'CENTER_LONG': row['LONGITUDE_CENTER_KALKULASI'],
                    'Distance_m': distance,
                    'Status': 'MELEBIHI TOLERANSI' if distance > 20 else 'DALAM TOLERANSI'
                })
            
            # Data untuk analisis umum
            coord_analysis_data.append({
                'Index': idx,
                'STN_NAME': row.get('STN_NAME', f'Data #{idx}'),
                'CLNT_NAME': row.get('CLNT_NAME', 'N/A'),
                'Distance_m': distance,
                'Status': 'MELEBIHI TOLERANSI' if distance > 20 else 'DALAM TOLERANSI'
            })
    
    if distances:
        # Metrics dengan informasi toleransi
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_distance = np.mean(distances)
            st.metric("Rata-rata Jarak", f"{avg_distance:.2f} m")
        
        with col2:
            max_distance = np.max(distances)
            st.metric("Jarak Maksimum", f"{max_distance:.2f} m")
        
        with col3:
            exceed_count = len(tolerance_exceeded)
            st.metric("🚨 Melebihi 20m", f"{exceed_count}")
        
        with col4:
            within_tolerance = valid_comparison - exceed_count
            st.metric("✅ Dalam Toleransi", f"{within_tolerance}")
        
        # Histogram jarak dengan garis toleransi
        fig_dist = px.histogram(
            x=distances,
            title="Distribusi Jarak antara Koordinat SID dan Center",
            nbins=30,
            labels={'x': 'Jarak (meter)', 'y': 'Frekuensi'}
        )
        
        # Tambahkan garis vertikal untuk toleransi 20m
        fig_dist.add_vline(x=20, line_dash="dash", line_color="red", 
                          annotation_text="Batas Toleransi 20m", 
                          annotation_position="top right")
        
        st.plotly_chart(fig_dist, use_container_width=True)
        
        # Tabel data yang melebihi toleransi
        if tolerance_exceeded:
            st.markdown("#### 🚨 Data yang Melebihi Toleransi 20 Meter")
            tolerance_df = pd.DataFrame(tolerance_exceeded)
            
            # Format kolom untuk tampilan yang lebih baik
            for col in ['SID_LAT', 'SID_LONG', 'CENTER_LAT', 'CENTER_LONG']:
                tolerance_df[col] = tolerance_df[col].round(6)
            tolerance_df['Distance_m'] = tolerance_df['Distance_m'].round(2)
            
            # Styling untuk tabel
            styled_tolerance_df = tolerance_df.style.apply(
                lambda x: ['background-color: #ffebee' if x.name % 2 == 0 else 'background-color: #fce4ec' 
                          for i in x], axis=1
            )
            
            st.dataframe(styled_tolerance_df, height=300, use_container_width=True)
            
            # Download button untuk data melebihi toleransi
            tolerance_csv = tolerance_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Data Melebihi Toleransi (CSV)",
                data=tolerance_csv,
                file_name=f"toleransi_exceeded_{selected_file.replace('.csv', '')}.csv",
                mime="text/csv"
            )
        else:
            st.success("✅ Semua data dalam toleransi 20 meter!")
        
        # Chart perbandingan dalam vs melebihi toleransi
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            # Pie chart toleransi
            tolerance_counts = pd.Series([len(tolerance_exceeded), valid_comparison - len(tolerance_exceeded)], 
                                       index=['Melebihi 20m', 'Dalam Toleransi'])
            
            fig_tolerance = px.pie(
                values=tolerance_counts.values,
                names=tolerance_counts.index,
                title="Distribusi Status Toleransi",
                color_discrete_map={
                    'Melebihi 20m': '#ff5252',
                    'Dalam Toleransi': '#4caf50'
                }
            )
            st.plotly_chart(fig_tolerance, use_container_width=True)
        
        with col_chart2:
            # Scatter plot jarak vs index
            coord_df = pd.DataFrame(coord_analysis_data)
            
            fig_scatter = px.scatter(
                coord_df,
                x=range(len(coord_df)),
                y='Distance_m',
                color='Status',
                title="Jarak per Data Point",
                labels={'x': 'Index Data', 'y': 'Jarak (meter)'},
                color_discrete_map={
                    'Melebihi 20m': '#ff5252',
                    'Dalam Toleransi': '#4caf50'
                },
                hover_data=['STN_NAME', 'CLNT_NAME']
            )
            
            # Tambahkan garis toleransi
            fig_scatter.add_hline(y=20, line_dash="dash", line_color="red", 
                                 annotation_text="Toleransi 20m")
            
            st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Statistik detail
        st.markdown("#### 📈 Statistik Detail Koordinat")
        
        stats_col1, stats_col2, stats_col3 = st.columns(3)
        
        with stats_col1:
            st.markdown("**📊 Statistik Jarak:**")
            st.write(f"• Minimum: {np.min(distances):.2f} m")
            st.write(f"• Median: {np.median(distances):.2f} m")
            st.write(f"• Standar Deviasi: {np.std(distances):.2f} m")
            
        with stats_col2:
            st.markdown("**🎯 Kategori Toleransi:**")
            within_5m = sum(1 for d in distances if d <= 5)
            within_10m = sum(1 for d in distances if 5 < d <= 10)
            within_20m = sum(1 for d in distances if 10 < d <= 20)
            above_20m = sum(1 for d in distances if d > 20)
            
            st.write(f"• ≤ 5m: {within_5m} data")
            st.write(f"• 5-10m: {within_10m} data")
            st.write(f"• 10-20m: {within_20m} data")
            st.write(f"• > 20m: {above_20m} data")
            
        with stats_col3:
            st.markdown("**⚠️ Persentase:**")
            total = len(distances)
            pct_within = ((total - len(tolerance_exceeded)) / total * 100) if total > 0 else 0
            pct_exceeded = (len(tolerance_exceeded) / total * 100) if total > 0 else 0
            
            st.write(f"• Dalam Toleransi: {pct_within:.1f}%")
            st.write(f"• Melebihi Toleransi: {pct_exceeded:.1f}%")
    
    else:
        st.warning("Tidak ada data koordinat yang valid untuk dibandingkan.")

# Data table dengan filter
st.markdown("### 📋 Data Tabel")
if not filtered_df.empty:
    # Pilih kolom penting untuk ditampilkan (yang tersedia)
    base_columns = ['SID_LAT', 'SID_LONG']
    optional_columns = [
        'STN_NAME', 'CLNT_NAME', 'CITY', 'STATUS_MYSPECTRA', 
        'Status Verifikasi UPT 2024', 'FREQ', 'ERP_PWR_DBM',
        'LATITUDE_CENTER_KALKULASI', 'LONGITUDE_CENTER_KALKULASI'
    ]
    
    display_columns = base_columns + [col for col in optional_columns if col in filtered_df.columns]
    display_df = filtered_df[display_columns].copy()
    
    # Format koordinat untuk tampilan yang lebih baik
    coord_cols = ['SID_LAT', 'SID_LONG', 'LATITUDE_CENTER_KALKULASI', 'LONGITUDE_CENTER_KALKULASI']
    for col in coord_cols:
        if col in display_df.columns:
            display_df[col] = display_df[col].round(6)
    
    st.dataframe(display_df, height=400, use_container_width=True)
    
    # Tombol download
    csv = filtered_df.to_csv(index=False)
    filename = f"filtered_data_{selected_file.replace('.csv', '')}_{selected_city}_{selected_clnt}.csv"
    st.download_button(
        label="📥 Download Data Terfilter (CSV)",
        data=csv,
        file_name=filename,
        mime="text/csv"
    )

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    f"🚀 Aplikasi Peta Interaktif Auto Load CSV | "
    f"📄 File: {selected_file} | "
    f"📊 Total Records: {len(df)} | "
    f"🎯 Filtered: {len(filtered_df)}"
    "</div>", 
    unsafe_allow_html=True
)