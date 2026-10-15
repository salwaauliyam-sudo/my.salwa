
import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================================
# 1. KONFIGURASI DASHBOARD
# ==========================================
st.set_page_config(
    page_title="Dashboard Fiskal Daerah",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Dashboard Fiskal Daerah")
st.caption("Analisis data fiskal dan indikator sosial-ekonomi daerah.")

# ==========================================
# 2. MEMANGGIL DAN MEMBACA DATASET CSV
# ==========================================
@st.cache_data
def load_data():
    df = pd.read_csv("dataset_fiskal_97_hipoFull.csv")

    df.columns = df.columns.str.strip()

    # Memastikan kolom tahun berbentuk angka
    df["Tahun"] = pd.to_numeric(df["Tahun"], errors="coerce")

    # Mengubah kolom numerik agar dapat dianalisis
    for col in df.columns:
        if col not in ["Kota"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


try:
    df = load_data()
except FileNotFoundError:
    st.error(
        "Dataset tidak ditemukan. Pastikan file "
        "'dataset_fiskal_97_hipoFull.csv' berada "
        "dalam folder yang sama dengan streamlit_app.py."
    )
    st.stop()
except Exception as e:
    st.error(f"Gagal membaca dataset: {e}")
    st.stop()

if df.empty:
    st.error("Dataset tidak memiliki data.")
    st.stop()

# Memastikan kolom utama tersedia
if not {"Kota", "Tahun"}.issubset(df.columns):
    st.error("Dataset harus memiliki kolom Kota dan Tahun.")
    st.stop()

st.success(f"Dataset berhasil dimuat: {len(df):,} baris data.")

# ==========================================
# 3. MENENTUKAN KATEGORI VARIABEL
# ==========================================
revenue_cols = [
    c for c in [
        "DBH_PAJAK", "DBH_SDA", "DBH_Lainnya",
        "DAU_Grant", "DAU_Earmark", "DAK_Fisik",
        "DAK_Nonfisik", "PAD"
    ] if c in df.columns
]

spending_cols = [
    c for c in [
        "bm_pendidikan", "bm_kesehatan",
        "bm_perumahan", "bm_lingkungan",
        "bm_ekonomi", "bm_infrastruktur",
        "bm_pariwisata", "bm_perlindungan_sosial"
    ] if c in df.columns
]

outcome_cols = [
    c for c in [
        "KEMISKINAN", "PENGANGGURAN",
        "KETIMPANGAN", "IPM", "PE"
    ] if c in df.columns
]

# ==========================================
# 4. FILTER KOTA DAN TAHUN
# ==========================================
st.sidebar.header("🔎 Filter Data")

cities = sorted(df["Kota"].dropna().astype(str).unique())

selected_cities = st.sidebar.multiselect(
    "Pilih kota",
    options=cities,
    default=cities
)

years = sorted(df["Tahun"].dropna().astype(int).unique())

if not years:
    st.error("Tidak ditemukan data tahun yang valid.")
    st.stop()

year_range = st.sidebar.slider(
    "Rentang tahun",
    min_value=min(years),
    max_value=max(years),
    value=(min(years), max(years)),
    step=1
)

metric_options = outcome_cols or [
    c for c in df.select_dtypes(include="number").columns
    if c != "Tahun"
]

if not metric_options:
    st.error("Tidak ditemukan kolom numerik untuk dianalisis.")
    st.stop()

default_metric = "IPM" if "IPM" in metric_options else metric_options[0]

selected_metric = st.sidebar.selectbox(
    "Pilih indikator sosial-ekonomi",
    options=metric_options,
    index=metric_options.index(default_metric)
)

# Membuat data hasil filter
filtered = df[
    df["Kota"].astype(str).isin(selected_cities)
    & df["Tahun"].between(year_range[0], year_range[1])
].copy()

if filtered.empty:
    st.warning("Data tidak ditemukan. Silakan ubah filter kota atau tahun.")
    st.stop()

# ==========================================
# 5. KPI RINGKAS
# ==========================================
k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "Jumlah kota terpilih",
    f"{filtered['Kota'].nunique():,}"
)

k2.metric(
    "Jumlah observasi",
    f"{len(filtered):,}"
)

k3.metric(
    "Tahun awal",
    f"{int(filtered['Tahun'].min())}"
)

k4.metric(
    "Tahun akhir",
    f"{int(filtered['Tahun'].max())}"
)

st.divider()

# ==========================================
# 6. TREN INDIKATOR
# ==========================================
st.subheader(f"📈 Tren {selected_metric}")

trend = (
    filtered.groupby("Tahun", as_index=False)[selected_metric]
    .mean()
)

fig_trend = px.line(
    trend,
    x="Tahun",
    y=selected_metric,
    markers=True,
    title=f"Rata-rata {selected_metric} per Tahun",
    labels={
        "Tahun": "Tahun",
        selected_metric: f"Rata-rata {selected_metric}"
    }
)

fig_trend.update_layout(hovermode="x unified")
st.plotly_chart(fig_trend, use_container_width=True)

# ==========================================
# 7. PERBANDINGAN KOTA DAN PENDAPATAN
# ==========================================
left, right = st.columns(2)

with left:
    st.subheader("🏙️ Perbandingan Antarkota")

    latest_year = int(filtered["Tahun"].max())

    latest = (
        filtered[filtered["Tahun"] == latest_year]
        .groupby("Kota", as_index=False)[selected_metric]
        .mean()
        .sort_values(selected_metric, ascending=False)
    )

    fig_city = px.bar(
        latest,
        x="Kota",
        y=selected_metric,
        title=f"{selected_metric} per Kota pada {latest_year}",
        labels={"Kota": "Kota", selected_metric: selected_metric}
    )

    fig_city.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_city, use_container_width=True)

with right:
    st.subheader("💰 Pendapatan dan Transfer")

    if revenue_cols:
        composition = (
            filtered[revenue_cols]
            .mean()
            .rename_axis("Komponen")
            .reset_index(name="Rata-rata")
            .sort_values("Rata-rata", ascending=False)
        )

        fig_comp = px.bar(
            composition,
            x="Komponen",
            y="Rata-rata",
            color="Komponen",
            title="Rata-rata Komponen Pendapatan dan Transfer"
        )

        fig_comp.update_layout(
            showlegend=False,
            xaxis_tickangle=-35
        )

        st.plotly_chart(fig_comp, use_container_width=True)
    else:
        st.info("Kolom pendapatan dan transfer tidak ditemukan.")

# ==========================================
# 8. ANALISIS BELANJA DAERAH
# ==========================================
if spending_cols:
    st.subheader("🏗️ Belanja Daerah Berdasarkan Fungsi")

    spending = (
        filtered[spending_cols]
        .mean()
        .rename_axis("Kategori Belanja")
        .reset_index(name="Rata-rata")
        .sort_values("Rata-rata", ascending=False)
    )

    fig_spending = px.bar(
        spending,
        x="Kategori Belanja",
        y="Rata-rata",
        color="Kategori Belanja",
        title="Perbandingan Rata-rata Belanja Daerah"
    )

    fig_spending.update_layout(
        showlegend=False,
        xaxis_tickangle=-35
    )

    st.plotly_chart(fig_spending, use_container_width=True)

# ==========================================
# 9. HUBUNGAN INDIKATOR SOSIAL-EKONOMI
# ==========================================
st.subheader("🔗 Hubungan Indikator Sosial-Ekonomi")

if len(outcome_cols) >= 2:
    x_options = outcome_cols

    default_x = next(
        (x for x in x_options if x != selected_metric),
        x_options[0]
    )

    x_metric = st.selectbox(
        "Indikator sumbu X",
        x_options,
        index=x_options.index(default_x)
    )

    y_metric = st.selectbox(
        "Indikator sumbu Y",
        x_options,
        index=(
            x_options.index(selected_metric)
            if selected_metric in x_options
            else 0
        )
    )

    scatter_data = filtered.dropna(
        subset=[x_metric, y_metric]
    )

    if not scatter_data.empty:
        fig_scatter = px.scatter(
            scatter_data,
            x=x_metric,
            y=y_metric,
            color="Kota",
            hover_data=["Tahun"],
            opacity=0.75,
            title=f"Hubungan {x_metric} dan {y_metric}"
        )

        st.plotly_chart(
            fig_scatter,
            use_container_width=True
        )

        if len(scatter_data) >= 3:
            corr = scatter_data[[x_metric, y_metric]].corr().iloc[0, 1]

            if pd.notna(corr):
                st.caption(
                    f"Korelasi Pearson: {corr:.3f}. "
                    "Korelasi tidak otomatis menunjukkan sebab-akibat."
                )
    else:
        st.info("Tidak ada data yang cukup untuk membuat grafik.")
else:
    st.info(
        "Diperlukan minimal dua indikator sosial-ekonomi."
    )

# ==========================================
# 10. TABEL DATA DAN UNDUHAN
# ==========================================
st.subheader("📋 Data Fiskal Terfilter")

with st.expander("Lihat data"):
    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True
    )

csv_bytes = filtered.to_csv(index=False).encode("utf-8")

st.download_button(
    label="⬇️ Unduh Data Hasil Filter (CSV)",
    data=csv_bytes,
    file_name="data_fiskal_terfilter.csv",
    mime="text/csv"
)

st.caption(
    "Dashboard menampilkan ringkasan dan rata-rata data sesuai filter "
    "yang dipilih. Perhatikan satuan dan definisi setiap variabel "
    "ketika menginterpretasikan hasil."
)
