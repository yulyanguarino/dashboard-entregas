import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output
import json
import urllib.request

# ==========================
# CARREGAR DADOS
# ==========================
df = pd.read_csv("base_dados.csv", encoding="utf-8-sig", sep=";")

# limpar colunas
df.columns = (
    df.columns
    .str.strip()
    .str.upper()
    .str.replace(r'\s+', '', regex=True)
)

col_uf = [c for c in df.columns if "UF" in c][0]

# datas e números
df["DATAEMISSAO"] = pd.to_datetime(df["DATAEMISSAO"], errors="coerce")
df["TME"] = pd.to_numeric(df["TME"], errors="coerce")

df = df.dropna(subset=["DATAEMISSAO"])

# ==========================
# GEOJSON BRASIL
# ==========================
url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
geojson = json.loads(urllib.request.urlopen(url).read())

# ==========================
# APP
# ==========================
app = Dash(__name__)

app.layout = html.Div(style={
    "fontFamily": "Arial",
    "backgroundColor": "#f5f7fb",
    "padding": "20px"
}, children=[

    # HEADER
    html.H1("📦 Dashboard de Entregas"),
    html.P("Mapa + filtros interativos"),

    # ==========================
    # FILTROS
    # ==========================
    html.Div(style={
        "display": "flex",
        "gap": "15px",
        "marginBottom": "15px"
    }, children=[

        dcc.DatePickerRange(
            id="data-range",
            start_date=df["DATAEMISSAO"].min(),
            end_date=df["DATAEMISSAO"].max(),
            display_format="DD/MM/YYYY"
        ),

        dcc.Dropdown(
            id="transportadora",
            options=[{"label": x, "value": x} for x in df["TRANSPORTADORA"].dropna().unique()],
            placeholder="Transportadora",
            clearable=True,
            style={"width": "250px"}
        )
    ]),

    # ==========================
    # LAYOUT PRINCIPAL
    # ==========================
    html.Div(style={"display": "flex", "gap": "20px"}, children=[

        # MAPA
        html.Div(style={
            "flex": "2",
            "backgroundColor": "white",
            "padding": "10px",
            "borderRadius": "10px",
            "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"
        }, children=[
            dcc.Graph(id="mapa")
        ]),

        # TABELA
        html.Div(style={
            "flex": "1",
            "backgroundColor": "white",
            "padding": "10px",
            "borderRadius": "10px",
            "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
            "maxHeight": "600px",
            "overflowY": "auto"
        }, children=[
            html.H3("Detalhes"),
            html.Div(id="tabela")
        ])

    ])
])

# ==========================
# FUNÇÃO FILTRO
# ==========================
def filtrar(df, data_range, transportadora):

    dff = df.copy()

    if data_range:
        start, end = data_range
        dff = dff[(dff["DATAEMISSAO"] >= start) & (dff["DATAEMISSAO"] <= end)]

    if transportadora:
        dff = dff[dff["TRANSPORTADORA"] == transportadora]

    return dff

# ==========================
# MAPA
# ==========================
@app.callback(
    Output("mapa", "figure"),
    Input("data-range", "start_date"),
    Input("data-range", "end_date"),
    Input("transportadora", "value")
)
def update_map(start, end, transp):

    dff = filtrar(df, (start, end), transp)

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
    fig.update_layout(margin=dict(l=0, r=0, t=30, b=0))

    return fig

# ==========================
# TABELA (VISUAL PROFISSIONAL)
# ==========================
@app.callback(
    Output("tabela", "children"),
    Input("mapa", "clickData"),
    Input("data-range", "start_date"),
    Input("data-range", "end_date"),
    Input("transportadora", "value")
)
def update_table(clickData, start, end, transp):

    dff = filtrar(df, (start, end), transp)

    if clickData:
        uf = clickData["points"][0]["location"]
        dff = dff[dff[col_uf] == uf]

    if dff.empty:
        return "Sem dados"

    return html.Div(style={"overflowX": "auto"}, children=[

        html.Table(
            style={
                "width": "100%",
                "borderCollapse": "collapse",
                "fontSize": "11px"
            },
            children=[

                # HEADER
                html.Tr([
                    html.Th(col, style={
                        "backgroundColor": "#f2f4f8",
                        "padding": "6px",
                        "textAlign": "left",
                        "borderBottom": "2px solid #ddd"
                    }) for col in dff.columns
                ])

            ] +

            # LINHAS
            [
                html.Tr([
                    html.Td(
                        str(dff.iloc[i][col]),
                        style={
                            "padding": "6px",
                            "borderBottom": "1px solid #eee",
                            "whiteSpace": "nowrap"
                        }
                    ) for col in dff.columns
                ]) for i in range(len(dff))
            ]
        )
    ])

# ==========================
# RUN
# ==========================
if __name__ == "__main__":
    app.run(debug=True)