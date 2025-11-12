import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO

# ---------------- 页面配置 ----------------
st.set_page_config(page_title="REITs Valuation SaaS", page_icon="🏢", layout="wide")

# ---------------- 多语言字典 ----------------
LANG = {
    "en": {
        "title": "🏢 REITs Valuation System (Income Approach)",
        "subtitle": "Simulate, compare and export REIT valuation reports.",
        "calc": "🚀 Run Valuation",
        "result": "Valuation Results",
        "export_excel": "📤 Export Excel",
        "export_pdf": "🧾 Export PDF Report",
        "scenario_chart": "Scenario Comparison",
        "base_rent": "Base Rent (RMB/m²/month)",
        "rent_growth": "Rent Growth Rate (%)",
        "occupancy": "Occupancy (%)",
        "cost_ratio": "Operating Cost Ratio (%)",
        "discount_rate": "Discount Rate (%)",
        "long_growth": "Terminal Growth Rate (%)",
        "term": "Valuation Period (years)",
        "area": "Gross Floor Area (m²)",
        "project": "Project Name",
        "simulate": "Scenario Simulation (± changes)"
    },
    "zh": {
        "title": "🏢 REITs 收益法估值系统",
        "subtitle": "可进行估值计算、情景对比并导出报告。",
        "calc": "🚀 开始计算估值",
        "result": "估值结果",
        "export_excel": "📤 导出 Excel",
        "export_pdf": "🧾 导出 PDF 报告",
        "scenario_chart": "情景对比图",
        "base_rent": "起始租金（元/㎡/月）",
        "rent_growth": "租金年增长率（%）",
        "occupancy": "出租率（%）",
        "cost_ratio": "运营成本率（%）",
        "discount_rate": "折现率（%）",
        "long_growth": "永续增长率（%）",
        "term": "收益期（年）",
        "area": "建筑面积（㎡）",
        "project": "项目名称",
        "simulate": "情景模拟（参数 ± 变化）"
    }
}

# ---------------- 语言选择 ----------------
lang_choice = st.sidebar.selectbox("🌐 Language / 语言", ["English", "中文"])
T = LANG["en" if lang_choice == "English" else "zh"]

# ---------------- 页面标题 ----------------
st.title(T["title"])
st.caption(T["subtitle"])
st.divider()

# ---------------- 参数输入 ----------------
col1, col2, col3 = st.columns(3)
with col1:
    base_rent = st.number_input(T["base_rent"], value=60.73)
    occupancy = st.number_input(T["occupancy"], value=98.0) / 100
    cost_ratio = st.number_input(T["cost_ratio"], value=15.5) / 100
with col2:
    rent_growth = st.number_input(T["rent_growth"], value=0.67) / 100
    discount_rate = st.number_input(T["discount_rate"], value=6.0) / 100
    long_growth = st.number_input(T["long_growth"], value=2.5) / 100
with col3:
    term = st.number_input(T["term"], value=64, step=1)
    area = st.number_input(T["area"], value=53606.58)
    project_name = st.text_input(T["project"], value="安居百泉阁")

simulate = st.checkbox(T["simulate"], value=True)
delta = st.slider("变化幅度(%)", 1, 20, 5)

# ---------------- 收益法函数 ----------------
def income_valuation(base_rent, rent_growth, occupancy, cost_ratio,
                     discount_rate, long_growth, term, area):
    nois = []
    for t in range(1, int(term) + 1):
        rent_t = base_rent * ((1 + rent_growth) ** t) * occupancy * area * 12
        cost_t = rent_t * cost_ratio
        nois.append(rent_t - cost_t)
    tv = nois[-1] * (1 + long_growth) / (discount_rate - long_growth)
    years = np.arange(1, int(term) + 1)
    pvs = np.array(nois) / ((1 + discount_rate) ** years)
    total_value = np.sum(pvs) + tv / ((1 + discount_rate) ** term)
    return nois, pvs, total_value

# ---------------- 计算 ----------------
if st.button(T["calc"]):
    nois, pvs, total_value = income_valuation(
        base_rent, rent_growth, occupancy, cost_ratio,
        discount_rate, long_growth, term, area
    )

    st.subheader(T["result"])
    col1, col2, col3 = st.columns(3)
    col1.metric("估值（万元）", f"{total_value / 1e4:,.2f}")
    col2.metric("平均 NOI（万元）", f"{np.mean(nois)/1e4:,.2f}")
    col3.metric("终值贡献率", f"{(1 - np.sum(pvs)/total_value)*100:.1f}%")

    # 图表
    df = pd.DataFrame({"年份": np.arange(1, int(term) + 1), "NOI": nois, "贴现现金流": pvs})
    st.line_chart(df.set_index("年份"))

    # 情景模拟
    if simulate:
        scenarios = {
            "Base": [base_rent, rent_growth, occupancy, cost_ratio, discount_rate, long_growth],
            "+Δ": [base_rent*(1+delta/100), rent_growth*(1+delta/100), occupancy*(1+delta/100), cost_ratio, discount_rate*(1-delta/100), long_growth*(1+delta/100)],
            "-Δ": [base_rent*(1-delta/100), rent_growth*(1-delta/100), occupancy*(1-delta/100), cost_ratio, discount_rate*(1+delta/100), long_growth*(1-delta/100)]
        }
        results = {}
        for s, vals in scenarios.items():
            _, _, v = income_valuation(*vals, term, area)
            results[s] = v / 1e4
        st.bar_chart(pd.DataFrame(results, index=["估值(万元)"]).T)

    # ---------------- Excel 导出 ----------------
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="ValuationData", index=False)
        summary = pd.DataFrame({
            "指标": ["估值(万元)", "平均NOI(万元)", "终值贡献(%)"],
            "数值": [total_value/1e4, np.mean(nois)/1e4, (1 - np.sum(pvs)/total_value)*100]
        })
        summary.to_excel(writer, sheet_name="Summary", index=False)
    output.seek(0)
    st.download_button(T["export_excel"], data=output, file_name=f"{project_name}_valuation.xlsx")

    # ---------------- PDF 报告导出 ----------------
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot(np.arange(1, int(term) + 1), nois, label="NOI")
    ax.plot(np.arange(1, int(term) + 1), pvs, label="PV")
    ax.legend(); ax.set_title("NOI & PV Trend"); ax.set_xlabel("Year"); ax.set_ylabel("Value (RMB)")
    chart_buf = BytesIO()
    plt.savefig(chart_buf, format="png"); chart_buf.seek(0)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"REITs Valuation Report - {project_name}", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 8, f"""
Project: {project_name}
Valuation: {total_value/1e4:,.2f} 万元
Average NOI: {np.mean(nois)/1e4:,.2f} 万元
Terminal Contribution: {(1 - np.sum(pvs)/total_value)*100:.1f}%
""")
    pdf.image(chart_buf, x=20, y=80, w=170)
    pdf_output = BytesIO(pdf.output(dest="S").encode("latin1"))
    st.download_button(T["export_pdf"], data=pdf_output, file_name=f"{project_name}_valuation.pdf", mime="application/pdf")
