from streamlit_folium import folium_static
import folium
import streamlit as st
import pandas as pd

@st.cache_data  
def load_data(path):
    df = pd.read_csv(path)
    return df

# Load data
pesanan = load_data("../data/data_pesanan_Brazilian_E-Commerce.csv")
lokasi_pelanggan = load_data("../data/lokasi_pelanggan.csv")
lokasi_penjual = load_data("../data/lokasi_penjual.csv")
lokasi_pelanggan_view=lokasi_pelanggan.head(1000)
lokasi_penjual_view=lokasi_penjual.head(3500)

pesanan['revenue'] = pesanan['order_item_id'] * pesanan['price']
pesanan['payment_type'] =  pesanan['payment_type'].fillna('others')


bulan_mapping = {
    1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'Mei', 6: 'Jun',
    7: 'Jul', 8: 'Agu', 9: 'Sep', 10: 'Okt', 11: 'Nov', 12: 'Des'
}
bulan_urut = list(bulan_mapping.values())  
pesanan['month_num'] = pesanan['month']  
pesanan['month'] = pesanan['month'].map(bulan_mapping)
pesanan['month'] = pd.Categorical(pesanan['month'], categories=bulan_urut, ordered=True)

# ========== SIDEBAR ==========
st.sidebar.header('Filter Data')
tahun_terpilih = st.sidebar.selectbox(
    'Pilih Tahun',
    options=sorted(pesanan['year'].unique())
)

bulan_terpilih = st.sidebar.selectbox(
    'Pilih Bulan',
    options=['All'] + bulan_urut,
    index=0
)
filtered_data = pesanan[pesanan['year'] == tahun_terpilih]
if bulan_terpilih != 'All':
  filtered_data = filtered_data[filtered_data['month'] == bulan_terpilih]

st.title("📊 Brazilian E-Commerce Dashboard")
# ========== KPI ==========
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Pendapatan", f" {filtered_data['revenue'].sum():,.2f}")
col2.metric("Avg Order Value", f" {filtered_data['revenue'].sum()/filtered_data['order_id'].nunique():,.2f}")
col3.metric("Avg Review", f"{filtered_data['review_score'].mean():.1f}/5.0")
col4.metric("Total Produk Terjual", f"{filtered_data['order_item_id'].sum()}")


## ========== LINE CHART TREN  ==========
pendapatan_bulanan = pesanan.groupby(['year', 'month'])['revenue'].sum().reset_index()
pendapatan_bulanan['growth_rate'] = pendapatan_bulanan.groupby('year')['revenue'].pct_change() * 100
pendapatan_bulanan = pendapatan_bulanan.sort_values(by=['year', 'month'])
pendapatan_bulanan_filtered = pendapatan_bulanan[pendapatan_bulanan['year'] == tahun_terpilih]
line_pendapatan = pendapatan_bulanan.pivot(index='month', columns='year', values='revenue')
line_pertumbuhan = pendapatan_bulanan_filtered.pivot(index='month', columns='year', values='growth_rate')

# # ========== KPI ==========
col1, col2 = st.columns(2)
col1.subheader('Trend Pendapatan Bulanan')
col1.line_chart(line_pendapatan)
col2.subheader(f' Growth Rate {tahun_terpilih}')
col2.line_chart(line_pertumbuhan)

# ========== BAR CHART KATEGORI PRODUK ==========
st.subheader('Top 5 Kategori Produk')
top_categories = filtered_data.groupby('product_category')['revenue'].sum().nlargest(5)
st.bar_chart(top_categories)

# ========== BAR CHART TIPE PEMBAYARAN ==========
st.subheader('Tren Tipe Pembayaran')
top_categories = filtered_data.groupby('payment_type')['order_id'].nunique()
st.bar_chart(top_categories)


# ========== PETA PERSEBARAN POPULASI ==========
st.subheader("Kota Persebaran Pembeli dan Pelanggan")
col1, col2 = st.columns(2)
col1.metric("Total Pelanggan", f" {lokasi_pelanggan['customer_unique_id'].count()}")
col2.metric("Total Penjual", f" {lokasi_penjual['seller_id'].count()}")
st.info('persebaran pada peta hanya sampel, diambil 1000 pelanggan dan 3500 penjual untuk mempercepat proses load', icon="ℹ️")
map = folium.Map(location=[-23.5505, -46.6333], zoom_start=10)
for idx, row in lokasi_pelanggan_view.iterrows():
    folium.CircleMarker(
        location=[row['geolocation_lat'], row['geolocation_lng']],
        radius=3,
        color='blue',
        fill=True,
        tooltip=f"Pelanggan: {row['customer_unique_id']}"
    ).add_to(map)
for idx, row in lokasi_penjual_view.iterrows():
    folium.CircleMarker(
        location=[row['geolocation_lat'], row['geolocation_lng']],
        radius=5,
        color='red',
        fill=True,
        tooltip=f"Penjual: {row['seller_id']}"
    ).add_to(map)

folium_static(map)
st.markdown(''':red[Merah] : Penjual''')
st.markdown(''':blue[Biru] : Pembeli''')

# # ========== DATA TABLE ==========
st.subheader('Preview Data')
st.dataframe(
    filtered_data[
        ['order_id', 'product_category', 'payment_value', 
         'review_score', 'shipping_limit_date', 'month']
    ].head(20),
    height=300
)

# ========== DOWNLOAD BUTTON ==========
st.download_button(
    label="Download Data Filtered",
    data=filtered_data.to_csv().encode('utf-8'),
    file_name='filtered_data.csv',
    mime='text/csv'
)