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
# FILTROS
# =========================
st.title("📦 Dashboard de Entregas")

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
# FILTRAR DADOS
# =========================
dff = df.copy()

if len(data_range) == 2:
    dff = dff[(dff["DATAEMISSAO"] >= pd.to_datetime(data_range[0])) &
              (dff["DATAEMISSAO"] <= pd.to_datetime(data_range[1]))]

if transportadora != "Todas":
    dff = dff[dff["TRANSPORTADORA"] == transportadora]

# =========================
# MAPA
# =========================
media = dff.groupby(col_uf)["TME"].mean().reset_index()

fig = px.choropleth(
    media,
    geojson=geojson,
    locations=col_uf,
    featureidkey="properties.sigla",
    color="TME",
    color_continuous_scale="Blues"
)

fig.update_geos(fitbounds="locations", visible=False)

st.plotly_chart(fig, use_container_width=True)

# =========================
# DETALHES
# =========================
st.subheader("📊 Detalhes")

uf_selecionado = st.selectbox(
    "Selecione o estado",
    ["Todos"] + sorted(dff[col_uf].unique())
)

if uf_selecionado != "Todos":
    dff = dff[dff[col_uf] == uf_selecionado]

st.dataframe(dff, use_container_width=True)