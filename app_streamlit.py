import streamlit as st
import pandas as pd
import plotly.express as px
import json
import urllib.request

# =========================
# CONFIG
# =========================
st.set_page_config(layout="wide", page_title="Dashboard de Entregas")

# =========================
# DADOS
# =========================
# 1. Carregamento com tratamento de encoding e separador
df = pd.read_csv("base_dados.csv", encoding="utf-8-sig", sep=";")

# 2. Limpeza das colunas (Removendo espaços extras e padronizando)
df.columns = (
    df.columns
    .str.strip()
    .str.upper()
    .str.replace(r'\s+', '', regex=True)
)

# 3. Tratamento de Strings e Datas (Onde estava o erro principal)
# Remove espaços em branco dos nomes das transportadoras (ex: "AMPLA ")
if "TRANSPORTADORA" in df.columns:
    df["TRANSPORTADORA"] = df["TRANSPORTADORA"].str.strip()

# Converte datas forçando o formato dia/mês/ano (dayfirst=True)
df["DATAEMISSAO"] = pd.to_datetime(df["DATAEMISSAO"], dayfirst=True, errors="coerce")
df["TME"] = pd.to_numeric(df["TME"], errors="coerce")

# Remove apenas se a data for realmente inválida (Nat)
df = df.dropna(subset=["DATAEMISSAO"])

# Identifica a coluna de UF dinamicamente
col_uf = [c for c in df.columns if "UF" in c][0]

# =========================
# GEOJSON BRASIL
# =========================
@st.cache_data # Cache para não baixar o mapa toda vez que filtrar
def load_geojson():
    url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
    return json.loads(urllib.request.urlopen(url).read())

geojson = load_geojson()

# =========================
# HEADER
# =========================
st.title("📦 Dashboard de Entregas")

# =========================
# FILTROS
# =========================
col1, col2 = st.columns(2)

with col1:
    # Garante que o intervalo inicial pegue todo o arquivo
    data_min = df["DATAEMISSAO"].min().date()
    data_max = df["DATAEMISSAO"].max().date()
    
    data_range = st.date_input(
        "Data de Emissão",
        [data_min, data_max]
    )

with col2:
    transportadora = st.selectbox(
        "Transportadora",
        options=["Todas"] + sorted(list(df["TRANSPORTADORA"].dropna().unique()))
    )

# =========================
# APLICAÇÃO DOS FILTROS
# =========================
dff = df.copy()

if len(data_range) == 2:
    dff = dff[
        (dff["DATAEMISSAO"].dt.date >= data_range[0]) &
        (dff["DATAEMISSAO"].dt.date <= data_range[1])
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
media_mapa = dff.groupby(col_uf)["TME"].mean().reset_index()

fig = px.choropleth(
    media_mapa,
    geojson=geojson,
    locations=col_uf,
    featureidkey="properties.sigla",
    color="TME",
    color_continuous_scale="Blues",
    hover_name=col_uf
)

fig.update_geos(
    scope="south america",
    fitbounds="locations",
    visible=False,
    showcountries=True,
    countrycolor="lightgray"
)

fig.update_traces(
    marker_line_color="black",
    marker_line_width=0.7,
    hovertemplate="<b>Estado: %{location}</b><br>TME: %{z:.2f}"
)

fig.update_layout(
    margin=dict(l=0, r=0, t=30, b=0),
    coloraxis_colorbar=dict(title="TME")
)

st.plotly_chart(fig, use_container_width=True)

# =========================
# SELEÇÃO DE ESTADO E TABELA
# =========================
st.subheader("📊 Detalhes das Entregas")

uf_selecionado = st.selectbox(
    "Filtrar tabela por estado",
    ["Todos"] + sorted(dff[col_uf].unique())
)

if uf_selecionado != "Todos":
    df_tabela = dff[dff[col_uf] == uf_selecionado]
else:
    df_tabela = dff

st.dataframe(df_tabela, use_container_width=True)