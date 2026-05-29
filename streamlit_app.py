import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

st.set_page_config(
    page_title="Mercado de Trabalho — Brasil",
    page_icon="📊",
    layout="wide",
)

# --- Paleta de cores ---
COR_TOTAL = "#37474F"
COR_HOMENS = "#1565C0"
COR_MULHERES = "#C2185B"
COR_DESOC = "#E53935"
COR_EMPREGO = "#00897B"
COR_INFORMAL = "#F9A825"
COR_CRISE_BG = "rgba(229,57,53,0.07)"
COR_COVID_BG = "rgba(120,120,120,0.10)"

# --- Rótulo de trimestre ---
def fmt_trimestre(dt):
    trim = {1: "T1", 4: "T2", 7: "T3", 10: "T4"}
    return f"{trim[dt.month]}/{dt.year}"


# --- Leitura dos dados ---
@st.cache_data
def carregar_dados():
    base = Path(__file__).parent / "data"

    def ler(nome):
        df = pd.read_csv(base / nome, sep=";")
        df["periodo"] = pd.to_datetime(df["periodo"])
        df["label"] = df["periodo"].apply(fmt_trimestre)
        return df

    desoc = ler("desocupacao.csv")
    emprego = ler("emprego.csv")
    informal = ler("informalidade.csv")
    return desoc, emprego, informal


desoc, emprego, informal = carregar_dados()

# --- Regiões anotadas (recessão e COVID) ---
REGIOES = [
    dict(
        x0="2015-01-01", x1="2017-07-01",
        fillcolor=COR_CRISE_BG, line_width=0,
        annotation="Recessão\n2015–2017",
        annotation_x="2016-01-01",
    ),
    dict(
        x0="2020-04-01", x1="2022-01-01",
        fillcolor=COR_COVID_BG, line_width=0,
        annotation="Dados\nausentesᵃ",
        annotation_x="2021-01-01",
    ),
]

def adicionar_regioes(fig, mostrar_anotacao=True):
    for r in REGIOES:
        fig.add_vrect(
            x0=r["x0"], x1=r["x1"],
            fillcolor=r["fillcolor"],
            line_width=r["line_width"],
        )
        if mostrar_anotacao:
            fig.add_annotation(
                x=r["annotation_x"],
                y=1.0,
                yref="paper",
                text=r["annotation"],
                showarrow=False,
                font=dict(size=9, color="#888"),
                align="center",
            )


# =============================================================================
# CABEÇALHO
# =============================================================================
st.title("Mercado de Trabalho Brasileiro")
st.caption(
    "Fonte: PNAD Contínua — IBGE  |  Dados trimestrais de 2012 a 2025  |  "
    "ᵃ Coleta suspensa durante a pandemia de COVID-19 (2020 T2 – 2022 T1)"
)
st.divider()

# =============================================================================
# ROW 1 — KPI CARDS
# =============================================================================
ultimo_desoc = desoc.iloc[-1]
penultimo_desoc = desoc.iloc[-2]
ultimo_emp = emprego.iloc[-1]
penultimo_emp = emprego.iloc[-2]
ultimo_inf = informal.iloc[-1]
penultimo_inf = informal.iloc[-2]

gap_atual = round(ultimo_desoc["mulheres"] - ultimo_desoc["homens"], 1)
gap_anterior = round(penultimo_desoc["mulheres"] - penultimo_desoc["homens"], 1)

col1, col2, col3, col4 = st.columns(4)

with col1:
    delta_desoc = round(ultimo_desoc["total"] - penultimo_desoc["total"], 1)
    st.metric(
        label="Desocupação",
        value=f"{ultimo_desoc['total']}%",
        delta=f"{delta_desoc:+.1f} p.p. vs tri. ant.",
        delta_color="inverse",
        help="Taxa de desocupação (% da PEA)",
    )

with col2:
    delta_emp = round(ultimo_emp["total"] - penultimo_emp["total"], 1)
    st.metric(
        label="Ocupação",
        value=f"{ultimo_emp['total']}%",
        delta=f"{delta_emp:+.1f} p.p. vs tri. ant.",
        delta_color="normal",
        help="Taxa de ocupação (% da pop. em idade ativa)",
    )

with col3:
    delta_inf = round(ultimo_inf["total"] - penultimo_inf["total"], 1)
    st.metric(
        label="Informalidade",
        value=f"{ultimo_inf['total']}%",
        delta=f"{delta_inf:+.1f} p.p. vs tri. ant.",
        delta_color="inverse",
        help="Taxa de informalidade (% dos ocupados sem carteira/CNPJ)",
    )

with col4:
    delta_gap = round(gap_atual - gap_anterior, 1)
    st.metric(
        label="Gap de Gênero (Desoc.)",
        value=f"+{gap_atual} p.p.",
        delta=f"{delta_gap:+.1f} p.p. vs tri. ant.",
        delta_color="inverse",
        help="Diferença entre taxa de desocupação de mulheres e homens",
    )

st.caption(f"Último dado disponível: **{ultimo_desoc['label']}**")
st.divider()

# =============================================================================
# ROW 2 — GRÁFICO HERÓI: Jornada do Desemprego
# =============================================================================
st.subheader("A Jornada do Desemprego (2012–2025)")
st.caption(
    "A taxa de desocupação mais que dobrou entre 2014 e 2017, atingindo quase 1 em cada 5 mulheres "
    "sem emprego. A área sombreada entre as linhas masculina e feminina revela o gap de gênero persistente."
)

fig_hero = go.Figure()

# Área do gap de gênero
fig_hero.add_trace(go.Scatter(
    x=desoc["periodo"], y=desoc["homens"],
    mode="lines", line=dict(width=0),
    showlegend=False, hoverinfo="skip",
    fillcolor="rgba(193,33,92,0.10)",
    fill=None,
    name="_homens_base",
))
fig_hero.add_trace(go.Scatter(
    x=desoc["periodo"], y=desoc["mulheres"],
    mode="lines", line=dict(width=0),
    fill="tonexty",
    fillcolor="rgba(193,33,92,0.10)",
    showlegend=False, hoverinfo="skip",
    name="_gap",
))

# Linhas principais
for col_name, nome, cor, largura, dash in [
    ("total",    "Total",    COR_TOTAL,    3, "solid"),
    ("homens",   "Homens",   COR_HOMENS,   2, "solid"),
    ("mulheres", "Mulheres", COR_MULHERES, 2, "solid"),
]:
    fig_hero.add_trace(go.Scatter(
        x=desoc["periodo"],
        y=desoc[col_name],
        mode="lines",
        name=nome,
        line=dict(color=cor, width=largura, dash=dash),
        customdata=desoc["label"],
        hovertemplate=f"<b>{nome}</b><br>%{{customdata}}<br>%{{y:.1f}}%<extra></extra>",
    ))

# Pico histórico
pico = desoc.loc[desoc["mulheres"].idxmax()]
fig_hero.add_annotation(
    x=pico["periodo"], y=pico["mulheres"],
    text=f"Pico: {pico['mulheres']}%<br>(mulheres, {pico['label']})",
    showarrow=True, arrowhead=2, arrowcolor=COR_MULHERES,
    font=dict(size=11, color=COR_MULHERES),
    bgcolor="white", bordercolor=COR_MULHERES, borderwidth=1,
    ax=40, ay=-40,
)

# Último ponto
ultimo = desoc.iloc[-1]
fig_hero.add_annotation(
    x=ultimo["periodo"], y=ultimo["total"],
    text=f"{ultimo['total']}%",
    showarrow=False,
    font=dict(size=11, color=COR_TOTAL, weight="bold"),
    xanchor="left", xshift=8,
)

adicionar_regioes(fig_hero)

fig_hero.update_layout(
    height=380,
    margin=dict(t=20, b=40, l=0, r=20),
    yaxis=dict(title="Taxa de desocupação (%)", ticksuffix="%", gridcolor="#EEEEEE"),
    xaxis=dict(showgrid=False),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    plot_bgcolor="white",
    paper_bgcolor="white",
    hovermode="x unified",
)
st.plotly_chart(fig_hero, width="stretch")

st.divider()

# =============================================================================
# ROW 3 — Ocupação | Informalidade
# =============================================================================
col_emp, col_inf = st.columns(2)

# --- Gráfico Ocupação ---
with col_emp:
    st.subheader("Taxa de Ocupação")
    st.caption("% da população em idade ativa que estava ocupada. Escala comprimida para revelar variações relevantes.")

    fig_emp = go.Figure()

    # Área de fundo (total)
    fig_emp.add_trace(go.Scatter(
        x=emprego["periodo"], y=emprego["total"],
        mode="lines",
        fill="tozeroy",
        fillcolor="rgba(0,137,123,0.10)",
        line=dict(color=COR_EMPREGO, width=2.5),
        name="Total",
        customdata=emprego["label"],
        hovertemplate="<b>Total</b><br>%{customdata}<br>%{y:.1f}%<extra></extra>",
    ))
    for col_name, nome, cor in [
        ("homens",   "Homens",   COR_HOMENS),
        ("mulheres", "Mulheres", COR_MULHERES),
    ]:
        fig_emp.add_trace(go.Scatter(
            x=emprego["periodo"], y=emprego[col_name],
            mode="lines",
            name=nome,
            line=dict(color=cor, width=1.8, dash="dot"),
            customdata=emprego["label"],
            hovertemplate=f"<b>{nome}</b><br>%{{customdata}}<br>%{{y:.1f}}%<extra></extra>",
        ))

    adicionar_regioes(fig_emp, mostrar_anotacao=False)

    fig_emp.update_layout(
        height=300,
        margin=dict(t=10, b=30, l=0, r=10),
        yaxis=dict(
            title="Taxa de ocupação (%)",
            ticksuffix="%",
            range=[38, 75],
            gridcolor="#EEEEEE",
        ),
        xaxis=dict(showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        plot_bgcolor="white", paper_bgcolor="white",
        hovermode="x unified",
    )
    st.plotly_chart(fig_emp, width="stretch")

# --- Gráfico Informalidade ---
with col_inf:
    st.subheader("Taxa de Informalidade")
    st.caption("% dos trabalhadores ocupados sem registro formal. Dados disponíveis a partir de 2015 T4.")

    fig_inf = go.Figure()

    # Linha de referência em 50%
    fig_inf.add_hline(
        y=50,
        line_dash="dot",
        line_color="#AAAAAA",
        annotation_text="50% — metade dos trabalhadores",
        annotation_position="top left",
        annotation_font=dict(size=10, color="#888"),
    )

    fig_inf.add_trace(go.Scatter(
        x=informal["periodo"], y=informal["total"],
        mode="lines",
        fill="tozeroy",
        fillcolor="rgba(249,168,37,0.12)",
        line=dict(color=COR_INFORMAL, width=2.5),
        name="Total",
        customdata=informal["label"],
        hovertemplate="<b>Total</b><br>%{customdata}<br>%{y:.1f}%<extra></extra>",
    ))
    for col_name, nome, cor in [
        ("homens",   "Homens",   COR_HOMENS),
        ("mulheres", "Mulheres", COR_MULHERES),
    ]:
        fig_inf.add_trace(go.Scatter(
            x=informal["periodo"], y=informal[col_name],
            mode="lines",
            name=nome,
            line=dict(color=cor, width=1.8, dash="dot"),
            customdata=informal["label"],
            hovertemplate=f"<b>{nome}</b><br>%{{customdata}}<br>%{{y:.1f}}%<extra></extra>",
        ))

    # Pico pós-pandemia
    pico_inf = informal.loc[informal["total"].idxmax()]
    fig_inf.add_annotation(
        x=pico_inf["periodo"], y=pico_inf["total"],
        text=f"Máxima pós-pandemia<br>{pico_inf['total']}%",
        showarrow=True, arrowhead=2, arrowcolor=COR_INFORMAL,
        font=dict(size=10, color=COR_INFORMAL),
        bgcolor="white", bordercolor=COR_INFORMAL, borderwidth=1,
        ax=-70, ay=-35,
    )

    # Região COVID (sem rótulo para não poluir)
    fig_inf.add_vrect(
        x0="2020-04-01", x1="2022-01-01",
        fillcolor=COR_COVID_BG, line_width=0,
    )

    fig_inf.update_layout(
        height=300,
        margin=dict(t=10, b=30, l=0, r=10),
        yaxis=dict(
            title="Taxa de informalidade (%)",
            ticksuffix="%",
            range=[38, 58],
            gridcolor="#EEEEEE",
        ),
        xaxis=dict(showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        plot_bgcolor="white", paper_bgcolor="white",
        hovermode="x unified",
    )
    st.plotly_chart(fig_inf, width="stretch")

st.divider()

# =============================================================================
# ROW 4 — Dumbbell Gênero | Scatter Correlação
# =============================================================================
col_db, col_sc = st.columns(2)

# --- Dumbbell Chart: gap de gênero no desemprego ---
with col_db:
    st.subheader("Desigualdade de Gênero no Desemprego")
    st.caption("Cada linha conecta a taxa masculina (azul) e feminina (rosa). O comprimento da linha é o gap.")

    PERIODOS_DUMBBELL = [
        "2012-01-01", "2014-10-01", "2017-01-01",
        "2019-10-01", "2022-04-01", "2024-10-01", "2025-10-01",
    ]
    db_df = desoc[desoc["periodo"].isin(pd.to_datetime(PERIODOS_DUMBBELL))].copy()
    db_df = db_df.sort_values("periodo")

    fig_db = go.Figure()

    for _, row in db_df.iterrows():
        gap = row["mulheres"] - row["homens"]
        alpha = 0.3 + 0.7 * (gap / db_df["mulheres"].max())
        fig_db.add_trace(go.Scatter(
            x=[row["homens"], row["mulheres"]],
            y=[row["label"], row["label"]],
            mode="lines",
            line=dict(color=f"rgba(193,33,92,{alpha:.2f})", width=3),
            showlegend=False,
            hoverinfo="skip",
        ))

    fig_db.add_trace(go.Scatter(
        x=db_df["homens"], y=db_df["label"],
        mode="markers+text",
        marker=dict(color=COR_HOMENS, size=12),
        text=[f"{v:.1f}%" for v in db_df["homens"]],
        textposition="middle left",
        name="Homens",
        hovertemplate="<b>Homens</b><br>%{y}<br>%{x:.1f}%<extra></extra>",
    ))
    fig_db.add_trace(go.Scatter(
        x=db_df["mulheres"], y=db_df["label"],
        mode="markers+text",
        marker=dict(color=COR_MULHERES, size=12),
        text=[f"{v:.1f}%" for v in db_df["mulheres"]],
        textposition="middle right",
        name="Mulheres",
        hovertemplate="<b>Mulheres</b><br>%{y}<br>%{x:.1f}%<extra></extra>",
    ))

    fig_db.update_layout(
        height=340,
        margin=dict(t=10, b=30, l=10, r=20),
        xaxis=dict(title="Taxa de desocupação (%)", ticksuffix="%", gridcolor="#EEEEEE"),
        yaxis=dict(showgrid=False, autorange="reversed"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        plot_bgcolor="white", paper_bgcolor="white",
    )
    st.plotly_chart(fig_db, width="stretch")

# --- Scatter: Correlação Ocupação × Desocupação ---
with col_sc:
    st.subheader("Trajetória: Ocupação vs. Desocupação")
    st.caption(
        "Cada ponto é um trimestre. A cor indica o tempo (azul escuro = 2012, verde = 2025). "
        "Emprego e desocupação medem realidades distintas — a crise e a recuperação não seguiram o mesmo caminho."
    )

    sc_df = desoc.merge(emprego, on=["periodo", "label"], suffixes=("_desoc", "_emp"))

    anos = sc_df["periodo"].dt.year
    ano_min, ano_max = anos.min(), anos.max()
    cores_scatter = [
        f"rgba({int(21 + (0 - 21) * (a - ano_min) / (ano_max - ano_min))},"
        f"{int(101 + (137 - 101) * (a - ano_min) / (ano_max - ano_min))},"
        f"{int(192 + (123 - 192) * (a - ano_min) / (ano_max - ano_min))},0.85)"
        for a in anos
    ]

    fig_sc = go.Figure()

    # Linha de trajetória
    fig_sc.add_trace(go.Scatter(
        x=sc_df["total_emp"], y=sc_df["total_desoc"],
        mode="lines",
        line=dict(color="#CCCCCC", width=1),
        showlegend=False, hoverinfo="skip",
    ))

    fig_sc.add_trace(go.Scatter(
        x=sc_df["total_emp"],
        y=sc_df["total_desoc"],
        mode="markers",
        marker=dict(
            color=anos,
            colorscale=[[0, "#1565C0"], [0.5, "#E53935"], [1.0, "#00897B"]],
            size=9,
            showscale=True,
            colorbar=dict(title="Ano", thickness=12, len=0.7),
        ),
        customdata=sc_df["label"],
        hovertemplate=(
            "<b>%{customdata}</b><br>"
            "Ocupação: %{x:.1f}%<br>"
            "Desocupação: %{y:.1f}%<extra></extra>"
        ),
        showlegend=False,
    ))

    # Destaque início e fim
    for idx, rotulo, cor in [(0, "2012 T1", COR_HOMENS), (-1, "2025 T4", COR_EMPREGO)]:
        row = sc_df.iloc[idx]
        fig_sc.add_annotation(
            x=row["total_emp"], y=row["total_desoc"],
            text=rotulo,
            showarrow=True, arrowhead=2, arrowcolor=cor,
            font=dict(size=10, color=cor),
            bgcolor="white", bordercolor=cor, borderwidth=1,
            ax=30, ay=-25,
        )

    fig_sc.update_layout(
        height=340,
        margin=dict(t=10, b=30, l=0, r=10),
        xaxis=dict(title="Taxa de ocupação (%)", ticksuffix="%", gridcolor="#EEEEEE"),
        yaxis=dict(title="Taxa de desocupação (%)", ticksuffix="%", gridcolor="#EEEEEE"),
        plot_bgcolor="white", paper_bgcolor="white",
    )
    st.plotly_chart(fig_sc, width="stretch")

# =============================================================================
# RODAPÉ
# =============================================================================
st.divider()
st.caption(
    "PNAD Contínua — Pesquisa Nacional por Amostra de Domicílios Contínua | IBGE | "
    "Dados trimestrais. Períodos 2020 T2 a 2022 T1 sem coleta por suspensão durante a pandemia de COVID-19."
)
