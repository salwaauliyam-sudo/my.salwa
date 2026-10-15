import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error

st.set_page_config(page_title="Prediksi Cerdas", page_icon="🧡", layout="wide")

CORAL, TEAL, NAVY = "#ff6b4a", "#1b998b", "#2b2d42"

# ---------- CSS ----------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&family=Playfair+Display:wght@700;900&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    #MainMenu, footer { visibility: hidden; }

    .masthead {
        border-top: 6px solid #2b2d42; border-bottom: 2px solid #2b2d42;
        padding: 1.2rem 0 1rem; margin-bottom: 1.4rem;
    }
    .masthead .kicker { letter-spacing: .25em; font-size: .75rem; font-weight: 700; color: #ff6b4a; }
    .masthead h1 {
        font-family: 'Playfair Display', serif; font-weight: 900;
        font-size: 3.2rem; line-height: 1.05; margin: .3rem 0 .2rem; color: #2b2d42;
    }
    .masthead p { margin: 0; color: #6b5b4d; font-size: 1.05rem; max-width: 760px; }

    .card {
        background: #ffffff; border-radius: 14px; padding: 1.1rem 1.3rem;
        box-shadow: 0 4px 0 #2b2d42; border: 2px solid #2b2d42;
        transition: transform .15s ease, box-shadow .15s ease;
    }
    .card:hover { transform: translate(-2px,-2px); box-shadow: 6px 6px 0 #2b2d42; }
    .card .lbl { font-size: .72rem; font-weight: 700; letter-spacing: .12em;
                 text-transform: uppercase; color: #8a7a6b; }
    .card .val { font-family: 'Playfair Display', serif; font-size: 2.2rem; font-weight: 900; color: #2b2d42; }
    .card .sub { font-size: .8rem; color: #8a7a6b; }
    .card.coral { border-top: 10px solid #ff6b4a; }
    .card.teal  { border-top: 10px solid #1b998b; }
    .card.navy  { border-top: 10px solid #2b2d42; }

    .note {
        background: #fff; border: 2px dashed #1b998b; border-radius: 12px;
        padding: 1rem 1.3rem; margin: 1rem 0; color: #2b2d42;
    }
    h2, h3 { font-family: 'Playfair Display', serif !important; color: #2b2d42; }
    .stRadio [role="radiogroup"] { gap: .5rem; }
    .stRadio label {
        background: #fff; border: 2px solid #2b2d42; border-radius: 999px;
        padding: .25rem 1rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def card(col, label, value, sub="", warna="coral"):
    col.markdown(
        f'<div class="card {warna}"><div class="lbl">{label}</div>'
        f'<div class="val">{value}</div><div class="sub">{sub}</div></div>',
        unsafe_allow_html=True,
    )


LAYOUT = dict(template="simple_white", paper_bgcolor="rgba(0,0,0,0)",
              plot_bgcolor="rgba(255,255,255,0.6)",
              font=dict(family="DM Sans", color=NAVY))

# ---------- Masthead ----------
st.markdown(
    """
    <div class="masthead">
        <div class="kicker">LAPORAN ANALISIS · REGRESI BERGANDA</div>
        <h1>Prediksi Cerdas</h1>
        <p>Temukan faktor mana yang paling memengaruhi hasil, lalu simulasikan
        skenario "bagaimana jika" dengan beberapa variabel sekaligus.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------- Data ----------
@st.cache_data
def data_contoh():
    rng = np.random.default_rng(7)
    n = 150
    luas = rng.uniform(30, 200, n)
    kamar = rng.integers(1, 6, n)
    umur = rng.uniform(0, 30, n)
    jarak = rng.uniform(1, 25, n)
    harga = (150 + 9 * luas + 60 * kamar - 7 * umur - 12 * jarak
             + rng.normal(0, 90, n))
    return pd.DataFrame({
        "Luas_m2": luas.round(1), "Jumlah_Kamar": kamar,
        "Umur_Bangunan": umur.round(1), "Jarak_ke_Pusat_km": jarak.round(1),
        "Harga_Juta": harga.round(1),
    })


st.sidebar.markdown("## 🧡 Pengaturan")
sumber = st.sidebar.radio("Sumber data", ["Data contoh (harga rumah)", "Upload CSV"])

if sumber == "Upload CSV":
    file = st.sidebar.file_uploader("Pilih file CSV", type="csv")
    if file is None:
        st.info("👈 Upload CSV di sidebar, atau pilih **Data contoh**.")
        st.stop()
    df = pd.read_csv(file)
else:
    df = data_contoh()

num = df.select_dtypes(include="number").columns.tolist()
if len(num) < 2:
    st.error("Data harus punya minimal 2 kolom numerik.")
    st.stop()

y_col = st.sidebar.selectbox("Yang ingin diprediksi (Y)", num, index=len(num) - 1)
pilihan_x = [c for c in num if c != y_col]
x_cols = st.sidebar.multiselect("Faktor penentu (X)", pilihan_x, default=pilihan_x[:4])
uji = st.sidebar.slider("Porsi data uji (%)", 10, 40, 20, step=5)
seed = st.sidebar.number_input("Random seed", value=42, step=1)

if not x_cols:
    st.warning("Pilih minimal satu variabel X di sidebar.")
    st.stop()

data = df[x_cols + [y_col]].dropna()
if len(data) < 15:
    st.error("Data terlalu sedikit (minimal 15 baris valid).")
    st.stop()

X, y = data[x_cols], data[y_col]
X_tr, X_te, y_tr, y_te = train_test_split(
    X, y, test_size=uji / 100, random_state=int(seed)
)
model = LinearRegression().fit(X_tr, y_tr)
p_tr, p_te = model.predict(X_tr), model.predict(X_te)

r2_tr, r2_te = r2_score(y_tr, p_tr), r2_score(y_te, p_te)
rmse_te = np.sqrt(mean_squared_error(y_te, p_te))
mae_te = mean_absolute_error(y_te, p_te)

# koefisien terstandar (perbandingan pengaruh antarvariabel)
std_coef = model.coef_ * X_tr.std().values / y_tr.std()
koef = pd.DataFrame({
    "Variabel": x_cols, "Koefisien": model.coef_, "Pengaruh_relatif": std_coef,
}).sort_values("Pengaruh_relatif", key=np.abs, ascending=False)

# ---------- KPI ----------
k1, k2, k3, k4 = st.columns(4)
card(k1, "R² data uji", f"{r2_te:.3f}", "akurasi pada data baru", "coral")
card(k2, "R² data latih", f"{r2_tr:.3f}", "kecocokan pada data latih", "teal")
card(k3, "RMSE uji", f"{rmse_te:,.2f}", "galat rata-rata (kuadrat)", "navy")
card(k4, "MAE uji", f"{mae_te:,.2f}", "galat rata-rata (absolut)", "coral")

teratas = koef.iloc[0]
selisih = r2_tr - r2_te
peringatan = (" Selisih R² latih dan uji cukup besar, ada indikasi <b>overfitting</b>."
              if selisih > 0.15 else "")
st.markdown(
    f'<div class="note">📝 Faktor paling berpengaruh pada <b>{y_col}</b> adalah '
    f'<b>{teratas["Variabel"]}</b> '
    f'({"meningkatkan" if teratas["Koefisien"] > 0 else "menurunkan"}). '
    f'Model menjelaskan <b>{r2_te*100:.1f}%</b> variasi pada data uji.{peringatan}</div>',
    unsafe_allow_html=True,
)

# ---------- Navigasi ----------
halaman = st.radio(
    "Menu", ["🔎 Faktor Utama", "🎯 Aktual vs Prediksi", "🧪 Simulasi", "🗂️ Data"],
    horizontal=True, label_visibility="collapsed",
)
st.write("")

# ---------- Halaman 1 ----------
if halaman == "🔎 Faktor Utama":
    st.subheader("Seberapa besar pengaruh tiap faktor?")
    st.caption("Pengaruh relatif memakai koefisien terstandar, jadi bisa dibandingkan "
               "meski satuan tiap variabel berbeda.")
    urut = koef.sort_values("Pengaruh_relatif")
    fig = go.Figure(go.Bar(
        x=urut["Pengaruh_relatif"], y=urut["Variabel"], orientation="h",
        marker_color=[TEAL if v > 0 else CORAL for v in urut["Pengaruh_relatif"]],
        text=[f"{v:+.2f}" for v in urut["Pengaruh_relatif"]], textposition="outside",
    ))
    fig.update_layout(**LAYOUT, height=120 + 70 * len(urut),
                      xaxis_title="Pengaruh relatif (teal = naik, koral = turun)",
                      margin=dict(l=10, r=40, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Persamaan model**")
    suku = " ".join(f"{c:+.3f}·{v}" for v, c in zip(x_cols, model.coef_))
    st.code(f"{y_col} = {model.intercept_:.3f} {suku}", language="text")

    if len(x_cols) > 1:
        kor = data[x_cols].corr()
        fh = px.imshow(kor, text_auto=".2f", zmin=-1, zmax=1,
                       color_continuous_scale=["#1b998b", "#fff8f0", "#ff6b4a"],
                       title="Korelasi antar faktor (cek multikolinearitas)")
        fh.update_layout(**LAYOUT, height=420)
        st.plotly_chart(fh, use_container_width=True)

# ---------- Halaman 2 ----------
elif halaman == "🎯 Aktual vs Prediksi":
    st.subheader("Seberapa dekat prediksi dengan kenyataan?")
    lo, hi = float(min(y.min(), p_te.min())), float(max(y.max(), p_te.max()))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[lo, hi], y=[lo, hi], mode="lines", name="Prediksi sempurna",
                             line=dict(color=NAVY, dash="dash")))
    fig.add_trace(go.Scatter(x=y_tr, y=p_tr, mode="markers", name="Data latih",
                             marker=dict(color=TEAL, size=8, opacity=.45)))
    fig.add_trace(go.Scatter(x=y_te, y=p_te, mode="markers", name="Data uji",
                             marker=dict(color=CORAL, size=11,
                                         line=dict(width=1.5, color=NAVY))))
    fig.update_layout(**LAYOUT, height=520, xaxis_title=f"{y_col} aktual",
                      yaxis_title=f"{y_col} prediksi", legend=dict(orientation="h", y=1.08))
    st.plotly_chart(fig, use_container_width=True)

    res = y_te - p_te
    fr = px.histogram(x=res, nbins=20, title="Sebaran galat pada data uji",
                      color_discrete_sequence=[CORAL])
    fr.update_layout(**LAYOUT, height=340, xaxis_title="Galat (aktual − prediksi)")
    st.plotly_chart(fr, use_container_width=True)

# ---------- Halaman 3 ----------
elif halaman == "🧪 Simulasi":
    st.subheader("Bagaimana jika...?")
    st.caption("Atur nilai tiap faktor, prediksi langsung dihitung.")
    kolom_in = st.columns(min(len(x_cols), 3))
    masukan = {}
    for i, c in enumerate(x_cols):
        lo, hi = float(X[c].min()), float(X[c].max())
        masukan[c] = kolom_in[i % len(kolom_in)].slider(
            c, lo, hi, float((lo + hi) / 2)
        )
    hasil = float(model.predict(pd.DataFrame([masukan]))[0])
    galat = 1.96 * rmse_te

    a, b = st.columns([1, 2])
    card(a, f"Prediksi {y_col}", f"{hasil:,.2f}", "estimasi titik", "teal")
    card(b, "Rentang wajar (±1,96 × RMSE uji)",
         f"{hasil - galat:,.2f}  –  {hasil + galat:,.2f}",
         "perkiraan kasar, bukan jaminan", "coral")

# ---------- Halaman 4 ----------
else:
    st.subheader("Data yang dipakai")
    out = data.copy()
    out["Prediksi"] = model.predict(X)
    st.dataframe(out, use_container_width=True, height=420)
    st.download_button("⬇️ Unduh hasil (CSV)", out.to_csv(index=False).encode("utf-8"),
                       file_name="hasil_prediksi.csv", mime="text/csv")
    st.dataframe(data.describe().T, use_container_width=True)
