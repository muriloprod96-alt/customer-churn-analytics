"""Create portfolio-ready KPIs, charts and an executive summary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


NAVY = "#0B1F3A"
BLUE = "#2563EB"
TEAL = "#0F766E"
RED = "#DC2626"
LIGHT = "#E8EEF7"


def _style() -> None:
    sns.set_theme(style="whitegrid", font_scale=1.0)
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.titleweight": "bold",
            "axes.titlecolor": NAVY,
            "axes.labelcolor": NAVY,
        }
    )


def create_outputs(data_path: Path, report_dir: Path) -> dict[str, float]:
    _style()
    report_dir.mkdir(parents=True, exist_ok=True)
    figures = report_dir / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    data = pd.read_csv(data_path)

    active = data[data["churn"] == 0]
    churned = data[data["churn"] == 1]
    summary = {
        "customers": int(len(data)),
        "churned_customers": int(data["churn"].sum()),
        "churn_rate": float(data["churn"].mean()),
        "active_mrr": float(active["monthly_charges"].sum()),
        "annual_revenue_at_risk": float(churned["annual_revenue"].sum()),
        "average_nps": float(data["nps"].mean()),
        "average_tenure_months": float(data["tenure_months"].mean()),
        "high_risk_active_customers": int(
            ((data["risk_segment"] == "Alto") & (data["churn"] == 0)).sum()
        ),
    }

    contract = (
        data.groupby("contract", observed=True)["churn"]
        .mean()
        .sort_values(ascending=False)
        .mul(100)
    )
    fig, ax = plt.subplots(figsize=(8, 4.8))
    contract.plot(kind="bar", color=[RED, BLUE, TEAL], ax=ax)
    ax.set_title("Taxa de churn por tipo de contrato")
    ax.set_xlabel("")
    ax.set_ylabel("Churn (%)")
    ax.tick_params(axis="x", rotation=0)
    ax.bar_label(ax.containers[0], fmt="%.1f%%", padding=4)
    sns.despine()
    fig.tight_layout()
    fig.savefig(figures / "churn_by_contract.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    risk = (
        data.groupby("risk_segment", observed=True)["churn"]
        .mean()
        .reindex(["Baixo", "Médio", "Alto"])
        .mul(100)
    )
    fig, ax = plt.subplots(figsize=(8, 4.8))
    risk.plot(kind="barh", color=[TEAL, "#F59E0B", RED], ax=ax)
    ax.set_title("Validação do segmento de risco")
    ax.set_xlabel("Churn (%)")
    ax.set_ylabel("")
    ax.bar_label(ax.containers[0], fmt="%.1f%%", padding=4)
    sns.despine()
    fig.tight_layout()
    fig.savefig(figures / "churn_by_risk_segment.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    heat = data.pivot_table(
        index="contract",
        columns="nps",
        values="churn",
        aggfunc="mean",
        observed=True,
    )
    fig, ax = plt.subplots(figsize=(10, 4.8))
    sns.heatmap(heat * 100, cmap="RdYlGn_r", annot=False, fmt=".0f", ax=ax)
    ax.set_title("Churn por contrato e NPS")
    ax.set_xlabel("NPS")
    ax.set_ylabel("Contrato")
    fig.tight_layout()
    fig.savefig(figures / "churn_contract_nps_heatmap.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    nps_curve = data.groupby("nps")["churn"].mean().mul(100)
    fig = plt.figure(figsize=(13, 8), facecolor="#F7F9FC")
    grid = fig.add_gridspec(3, 6, height_ratios=[0.8, 2.2, 2.2], hspace=0.65, wspace=0.8)
    cards = [
        ("CLIENTES", f"{summary['customers']:,}"),
        ("CHURN", f"{summary['churn_rate']:.1%}"),
        ("MRR ATIVO", f"R$ {summary['active_mrr']/1000:.0f} mil"),
        ("ALTO RISCO ATIVO", f"{summary['high_risk_active_customers']:,}"),
    ]
    for index, (label, value) in enumerate(cards):
        ax = fig.add_subplot(grid[0, index * 6 // 4:(index + 1) * 6 // 4])
        ax.set_facecolor("white")
        ax.text(0.05, 0.72, label, transform=ax.transAxes, color="#64748B", fontsize=9, weight="bold")
        ax.text(0.05, 0.23, value, transform=ax.transAxes, color=NAVY, fontsize=19, weight="bold")
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_color("#DCE4EF")

    ax1 = fig.add_subplot(grid[1:, :3])
    contract.sort_values().plot(kind="barh", color=[TEAL, BLUE, RED], ax=ax1)
    ax1.set_title("Churn por contrato", loc="left")
    ax1.set_xlabel("Churn (%)")
    ax1.set_ylabel("")
    ax1.bar_label(ax1.containers[0], fmt="%.1f%%", padding=4)
    sns.despine(ax=ax1)

    ax2 = fig.add_subplot(grid[1, 3:])
    risk.plot(kind="bar", color=[TEAL, "#F59E0B", RED], ax=ax2)
    ax2.set_title("Churn por segmento de risco", loc="left")
    ax2.set_xlabel("")
    ax2.set_ylabel("Churn (%)")
    ax2.tick_params(axis="x", rotation=0)
    sns.despine(ax=ax2)

    ax3 = fig.add_subplot(grid[2, 3:])
    ax3.plot(nps_curve.index, nps_curve.values, marker="o", color=BLUE, linewidth=2)
    ax3.fill_between(nps_curve.index, nps_curve.values, color=BLUE, alpha=0.10)
    ax3.set_title("Churn por NPS", loc="left")
    ax3.set_xlabel("NPS")
    ax3.set_ylabel("Churn (%)")
    ax3.set_xticks(range(0, 11))
    sns.despine(ax=ax3)

    fig.suptitle("Customer Churn Analytics", x=0.06, y=0.985, ha="left", color=NAVY, fontsize=18, weight="bold")
    fig.text(0.06, 0.943, "Visão executiva da retenção de clientes | Dados sintéticos", color="#64748B", fontsize=10)
    fig.savefig(figures / "portfolio_overview.png", dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)

    report = {
        "summary": summary,
        "churn_by_contract": contract.round(4).to_dict(),
        "churn_by_risk_segment": risk.round(4).to_dict(),
    }
    (report_dir / "kpis.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    highest_contract = contract.index[0]
    highest_contract_rate = contract.iloc[0]
    executive = f"""# Resumo executivo

## Visão geral

- **{summary['customers']:,} clientes** analisados.
- **Taxa de churn:** {summary['churn_rate']:.1%}.
- **MRR ativo:** R$ {summary['active_mrr']:,.2f}.
- **Receita anual associada aos cancelamentos:** R$ {summary['annual_revenue_at_risk']:,.2f}.
- **Clientes ativos classificados como alto risco:** {summary['high_risk_active_customers']:,}.

## Principais achados

1. O contrato **{highest_contract}** apresentou o maior churn ({highest_contract_rate:.1f}%).
2. NPS baixo, recorrência de chamados, atrasos e inatividade digital concentraram risco.
3. Débito automático e contratos de maior duração estiveram associados a maior retenção.

## Recomendações

1. Criar uma régua de retenção para clientes mensais de alto risco nos primeiros seis meses.
2. Acionar recuperação de experiência após o terceiro chamado de suporte.
3. Incentivar débito automático e migração para plano anual com teste controlado.
4. Medir uplift, receita preservada e ROI com grupo de controle.

> Dados sintéticos. Os resultados demonstram método analítico e não representam uma empresa real.
"""
    (report_dir / "executive_summary.md").write_text(executive, encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data", type=Path, default=Path("data/processed/customer_churn_clean.csv")
    )
    parser.add_argument("--reports", type=Path, default=Path("reports"))
    args = parser.parse_args()
    summary = create_outputs(args.data, args.reports)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
