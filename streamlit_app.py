# KPI ringkas
k1, k2, k3, k4 = st.columns(4)
k1.metric("Jumlah kota terpilih", f"{filtered['Kota'].nunique():,}")
k2.metric("Jumlah observasi", f"{len(filtered):,}")
k3.metric("Tahun awal", f"{int(filtered['Tahun'].min())}")
k4.metric("Tahun akhir", f"{int(filtered['Tahun'].max())}")

st.divider()

# Tren indikator
st.subheader(f"📈 Tren {selected_metric}")
trend = filtered.groupby("Tahun", as_index=False)[selected_metric].mean()
fig_trend = px.line(
    trend, x="Tahun", y=selected_metric, markers=True,
    labels={"Tahun": "Tahun", selected_metric: f"Rata-rata {selected_metric}"},
    title=f"Rata-rata {selected_metric} per tahun untuk kota terpilih"
)
fig_trend.update_layout(hovermode="x unified")
st.plotly_chart(fig_trend, use_container_width=True)

left, right = st.columns(2)

with left:
    st.subheader("🏙️ Perbandingan antarkota")
    latest_year = int(filtered["Tahun"].max())
    latest = filtered[filtered["Tahun"] == latest_year].groupby("Kota", as_index=False)[selected_metric].mean()
    latest = latest.sort_values(selected_metric, ascending=False)
    fig_city = px.bar(
        latest, x="Kota", y=selected_metric,
        labels={"Kota": "Kota", selected_metric: selected_metric},
        title=f"{selected_metric} per kota pada {latest_year}"
    )
    fig_city.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_city, use_container_width=True)

with right:
    st.subheader("💰 Komposisi pendapatan/transfer")
    composition_cols = revenue_cols
    if composition_cols:
        composition = filtered[composition_cols].mean().reset_index()
        composition.columns = ["Komponen", "Rata-rata"]
        composition = composition.sort_values("Rata-rata", ascending=False)
        fig_comp = px.bar(
            composition, x="Komponen", y="Rata-rata", color="Komponen",
            title="Rata-rata komponen pendapatan dan transfer",
            labels={"Komponen": "Komponen", "Rata-rata": "Nilai rata-rata"}
        )
        fig_comp.update_layout(showlegend=False, xaxis_tickangle=-35)
        st.plotly_chart(fig_comp, use_container_width=True)
    else:
        st.info("Kolom pendapatan/transfer tidak ditemukan dalam dataset.")

# Belanja berdasarkan fungsi
if spending_cols:
    st.subheader("🏗️ Rata-rata belanja berdasarkan fungsi")
    spending = filtered[spending_cols].mean().reset_index()
    spending.columns = ["Kategori belanja", "Rata-rata"]
    spending = spending.sort_values("Rata-rata", ascending=False)
    fig_spending = px.bar(
        spending, x="Kategori belanja", y="Rata-rata", color="Kategori belanja",
        labels={"Kategori belanja": "Kategori belanja", "Rata-rata": "Nilai rata-rata"},
        title="Perbandingan rata-rata kategori belanja"
    )
    fig_spending.update_layout(showlegend=False, xaxis_tickangle=-35)
    st.plotly_chart(fig_spending, use_container_width=True)

# Hubungan dua indikator
st.subheader("🔗 Hubungan indikator sosial-ekonomi")
if len(outcome_cols) >= 2:
    x_options = outcome_cols
    default_x = "PE" if "PE" in x_options and selected_metric != "PE" else next(
        (x for x in x_options if x != selected_metric), x_options[0]
    )
    x_metric = st.selectbox("Indikator sumbu X", x_options, index=x_options.index(default_x))
    y_metric = st.selectbox(
        "Indikator sumbu Y", x_options,
        index=x_options.index(selected_metric) if selected_metric in x_options else 0
    )
    scatter_data = filtered.dropna(subset=[x_metric, y_metric])
    fig_scatter = px.scatter(
        scatter_data, x=x_metric, y=y_metric, color="Kota",
        hover_data=["Tahun"], opacity=0.75,
        title=f"Hubungan {x_metric} dan {y_metric}"
    )
    st.plotly_chart(fig_scatter, use_container_width=True)
    if len(scatter_data) >= 3:
        corr = scatter_data[[x_metric, y_metric]].corr().iloc[0, 1]
        st.caption(f"Korelasi Pearson pada data terfilter: {corr:.3f}. Korelasi tidak otomatis menunjukkan hubungan sebab-akibat.")
else:
    st.info("Diperlukan minimal dua kolom indikator sosial-ekonomi untuk membuat scatter plot.")

# Tabel data
with st.expander("📋 Lihat data yang sudah difilter"):
    st.dataframe(filtered, use_container_width=True, hide_index=True)

csv_bytes = filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Unduh data hasil filter (CSV)",
    data=csv_bytes,
    file_name="data_fiskal_terfilter.csv",
    mime="text/csv"
)

st.caption("Catatan: grafik menampilkan rata-rata dari baris data yang masuk filter. Pastikan satuan dan definisi setiap variabel sesuai dengan dokumentasi dataset.")
