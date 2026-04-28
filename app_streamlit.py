import streamlit as st
import pandas as pd
import plotly.express as px
import json
import urllib.request

# =========================
# CONFIG
# =========================
st.set_page_config(layout="wide")

# =========================
# DADOS
# =========================
df = pd.read_csv("base_dados.csv", encoding="utf-8-sig", sep=";")

df.columns = (
    df.columns
    .str.strip()
    .str.upper()
    .str.replace(r'\s+', '', regex=True)
)

col_uf = [c for c in df.columns if "UF" in c][0]

df["DATAEMISSAO"] = pd.to_datetime(df["DATAEMISSAO"], errors="coerce")
df["TME"] = pd.to_numeric(df["TME"], errors="coerce")

df = df.dropna(subset=["DATAEMISSAO"])

# =========================
# GEOJSON BRASIL
# =========================
url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
geojson = json.loads(urllib.request.urlopen(url).read())

# =========================
# HEADER
# =========================
st.title("📦 Dashboard de Entregas")

# =========================
# FILTROS
# =========================
col1, col2 = st.columns(2)

with col1:
    data_range = st.date_input(
        "Data de Emissão",
        [df["DATAEMISSAO"].min(), df["DATAEMISSAO"].max()]
    )

with col2:
    transportadora = st.selectbox(
        "Transportadora",
        options=["Todas"] + list(df["TRANSPORTADORA"].dropna().unique())
    )

# =========================
# FILTRO BASE
# =========================
dff = df.copy()

if len(data_range) == 2:
    dff = dff[
        (dff["DATAEMISSAO"] >= pd.to_datetime(data_range[0])) &
        (dff["DATAEMISSAO"] <= pd.to_datetime(data_range[1]))
    ]

if transportadora != "Todas":
    dff = dff[dff["TRANSPORTADORA"] == transportadora]

# =========================
# KPIs
# =========================
total_entregas = len(dff)
media_tme = round(dff["TME"].mean(), 2) if len(dff) > 0 else 0
estados_ativos = dff[col_uf].nunique()

k1, k2, k3 = st.columns(3)

k1.metric("📦 Total Entregas", total_entregas)
k2.metric("⏱ Média TME", media_tme)
k3.metric("📍 Estados Ativos", estados_ativos)

st.markdown("---")

# =========================
# MAPA BRASIL
# =========================
media = dff.groupby(col_uf)["TME"].mean().reset_index()

fig = px.choropleth(
    media,
    geojson=geojson,
    locations=col_uf,
    featureidkey="properties.sigla",
    color="TME",
    color_continuous_scale="Blues",
    hover_name=col_uf
)

# 🔥 MELHORIA VISUAL IMPORTANTE
fig.update_geos(
    scope="south america",
    fitbounds="locations",
    visible=False,
    showcountries=True,
    countrycolor="lightgray"
)

fig.update_traces(
    marker_line_color="black",   # borda dos estados
    marker_line_width=0.7,
    hovertemplate="<b>Estado: %{location}</b><br>TME: %{z:.2f}"
)

fig.update_layout(
    margin=dict(l=0, r=0, t=30, b=0),
    paper_bgcolor="white",
    plot_bgcolor="white",
    coloraxis_colorbar=dict(title="TME")
)

st.plotly_chart(fig, use_container_width=True)

# =========================
# SELEÇÃO DE ESTADO
# =========================
uf_selecionado = st.selectbox(
    "Selecione o estado (opcional)",
    ["Todos"] + sorted(dff[col_uf].unique())
)

if uf_selecionado != "Todos":
    dff = dff[dff[col_uf] == uf_selecionado]

# =========================
# TABELA
# =========================
st.subheader("📊 Detalhes das Entregas")

st.dataframe(dff, use_container_width=True)