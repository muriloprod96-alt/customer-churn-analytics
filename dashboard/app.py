"""Interactive Streamlit dashboard for the churn portfolio project."""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "processed" / "customer_churn_clean.csv"

st.set_page_config(
    page_title="Customer Churn Analytics",
    page_icon="📊",
    layout="wide",
)

st.markdown(
    """
    <style>
      .block-container {padding-top: 1.5rem;}
      [data-testid="stMetric"] {background:#F5F8FC; border:1px solid #E3EAF4;
        padding:14px; border-radius:12px;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data() -> pd.DataFrame:
    return pd.read_csv(DATA_PATH)


data = load_data()
st.title("Customer Churn Analytics")
st.caption("Dashboard executivo | Dados sintéticos | Python + SQL + Machine Learning")

with st.sidebar:
    st.header("Filtros")
    regions = st.multiselect("Região", sorted(data["region"].unique()))
    plans = st.multiselect("Plano", sorted(data["plan"].unique()))
    contracts = st.multiselect("Contrato", sorted(data["contract"].unique()))
    risk = st.multiselect("Risco", ["Baixo", "Médio", "Alto"])

filtered = data.copy()
for column, selected in {
    "region": regions,
    "plan": plans,
    "contract": contracts,
    "risk_segment": risk,
}.items():
    if selected:
        filtered = filtered[filtered[column].isin(selected)]

if filtered.empty:
    st.warning("Nenhum cliente corresponde aos filtros selecionados.")
    st.stop()

active = filtered[filtered["churn"] == 0]
col1, col2, col3, col4 = st.columns(4)
col1.metric("Clientes", f"{len(filtered):,}".replace(",", "."))
col2.metric("Churn", f"{filtered['churn'].mean():.1%}".replace(".", ","))
col3.metric("MRR ativo", f"R$ {active['monthly_charges'].sum():,.0f}".replace(",", "."))
col4.metric(
    "Ativos em alto risco",
    f"{((filtered['risk_segment'] == 'Alto') & (filtered['churn'] == 0)).sum():,}".replace(",", "."),
)

left, right = st.columns(2)
contract = (
    filtered.groupby("contract", as_index=False)["churn"].mean().sort_values("churn")
)
contract["churn"] *= 100
left.plotly_chart(
    px.bar(
        contract,
        x="churn",
        y="contract",
        orientation="h",
        text_auto=".1f",
        color="churn",
        color_continuous_scale=["#0F766E", "#F59E0B", "#DC2626"],
        labels={"churn": "Churn (%)", "contract": "Contrato"},
        title="Churn por contrato",
    ).update_layout(coloraxis_showscale=False),
    use_container_width=True,
)

risk_table = (
    filtered.groupby("risk_segment", observed=True, as_index=False)["churn"].mean()
)
risk_table["churn"] *= 100
right.plotly_chart(
    px.bar(
        risk_table,
        x="risk_segment",
        y="churn",
        text_auto=".1f",
        category_orders={"risk_segment": ["Baixo", "Médio", "Alto"]},
        color="risk_segment",
        color_discrete_map={"Baixo": "#0F766E", "Médio": "#F59E0B", "Alto": "#DC2626"},
        labels={"churn": "Churn (%)", "risk_segment": "Risco"},
        title="Validação do segmento de risco",
    ).update_layout(showlegend=False),
    use_container_width=True,
)

left, right = st.columns(2)
left.plotly_chart(
    px.box(
        filtered,
        x="churn",
        y="nps",
        color="churn",
        color_discrete_map={0: "#2563EB", 1: "#DC2626"},
        labels={"churn": "Churn", "nps": "NPS"},
        title="Distribuição de NPS por status",
    ).update_layout(showlegend=False, xaxis_tickvals=[0, 1], xaxis_ticktext=["Ativo", "Churn"]),
    use_container_width=True,
)
right.plotly_chart(
    px.scatter(
        filtered,
        x="tenure_months",
        y="monthly_charges",
        color="churn",
        opacity=0.55,
        color_discrete_map={0: "#2563EB", 1: "#DC2626"},
        labels={
            "tenure_months": "Tempo de relacionamento (meses)",
            "monthly_charges": "Mensalidade (R$)",
            "churn": "Churn",
        },
        title="Mensalidade × tempo de relacionamento",
    ),
    use_container_width=True,
)

st.subheader("Clientes ativos prioritários")
priority = active.sort_values(
    ["risk_score", "monthly_charges"], ascending=[False, False]
).head(20)
st.dataframe(
    priority[
        [
            "customer_id",
            "region",
            "plan",
            "contract",
            "monthly_charges",
            "nps",
            "support_tickets",
            "last_login_days",
            "risk_score",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)

