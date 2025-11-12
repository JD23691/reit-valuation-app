import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO
from datetime import datetime
import os

logo_path = "logo.png"
if os.path.exists(logo_path):
    pdf.image(logo_path, x=80, y=25, w=50)
else:
    pdf.set_font("Arial", "I", 12)
    pdf.cell(0, 10, "(No logo found — add logo.png to project folder)", ln=True, align="C")
# 页面设置
st.set_page_config(page_title="REITs Valuation SaaS", page_icon="🏢", layout="wide")

# 多语言字典
LANG = {
    "en": {
        "title": "🏢 REITs Valuation System (Income Approach)",
        "subtitle": "Simulate, compare, and export professional REIT valuation reports.",
        "calc": "🚀 Run Valuation",
        "result": "Valuation Results",
        "export_pdf": "🧾 Export PDF Report",
        "project": "Project Name",
        "base_rent": "Base Rent (RMB/m²/month)",
        "rent_growth": "Rent Growth Rate (%)",
        "occupancy": "Occupancy (%)",
        "cost_ratio": "Operating Cost Ratio (%)",
        "discount_rate": "Discount Rate (%)",
        "long_growth": "Terminal Growth Rate (%)",
        "term": "Valuation Period (years)",
        "area": "Gross Floor Area (m²)",
        "simulate": "Scenario Simulation (± changes)",
        "valuation": "Valuation (10k RMB)",
        "avg_noi": "Average NOI (10k RMB)",
        "terminal": "Terminal Share (%)",
        "chart": "NOI & PV Trend",
        "scenario_chart": "Scenario Valuation Comparison"
    },
    "zh": {
        "title": "🏢 REITs 收益法估值系统",
        "subtitle": "可进行估值计算、情景对比并导出专业报告。",
        "calc": "🚀 开始计算估值",
        "result": "估值结果",
        "export_pdf": "🧾 导出 PDF 报告",
        "project": "项目名称",
        "base_rent": "起始租金（元/㎡/月）",
        "rent_growth": "租金年增长率（%）",
        "occupancy": "出租率（%）",
        "cost_ratio": "运营成本率（%）",
        "discount_rate": "折现率（%）",
        "long_growth": "永续增长率（%）",
        "term": "收益期（年）",
        "area": "建筑面积（㎡）",
        "simulate": "情景模拟（参数 ± 变化）",
        "valuation": "估值（万元）",
        "avg_noi": "平均 NOI（万元）",
        "terminal": "终值贡献 (%)",
        "chart": "NOI 与贴现现金流趋势",
        "scenario_chart": "情景估值对比"
    }
}

# 语言选择
lang_choice = st.sidebar.selectbox("🌐 Language / 语言", ["English", "中文"])
T = LANG["en" if lang_choice == "English" else "zh"]

# 页面标题
st.title(T["title"])
st.caption(T["subtitle"])
st.divider()

# 参数输入
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

# 核心估值函数
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

# 执行计算
if st.button(T["calc"]):
    nois, pvs, total_value = income_valuation(
        base_rent, rent_growth, occupancy, cost_ratio,
        discount_rate, long_growth, term, area
    )

    st.subheader(T["result"])
    col1, col2, col3 = st.columns(3)
    col1.metric(T["valuation"], f"{total_value / 1e4:,.2f}")
    col2.metric(T["avg_noi"], f"{np.mean(nois)/1e4:,.2f}")
    col3.metric(T["terminal"], f"{(1 - np.sum(pvs)/total_value)*100:.1f}")

    # 图表
    df = pd.DataFrame({"Year": np.arange(1, int(term) + 1), "NOI": nois, "PV": pvs})
    st.line_chart(df.set_index("Year"))

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

    # ---------------- PDF 报告生成 ----------------
    # 折现现金流图
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot(df["Year"], df["NOI"], label="NOI", color="blue")
    ax.plot(df["Year"], df["PV"], label="PV", color="green")
    ax.legend(); ax.set_title(T["chart"]); ax.set_xlabel("Year"); ax.set_ylabel("Value (RMB)")
    chart_buf = BytesIO()
    plt.savefig(chart_buf, format="png")
    chart_buf.seek(0)

    # 创建 PDF
    pdf = FPDF()
    pdf.add_page()

    # 封面页
    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 10, "REITs Valuation Report", ln=True, align="C")
    pdf.ln(60)
    pdf.set_font("Arial", "", 14)
    pdf.multi_cell(0, 10, f"""
Project: {project_name}
Date: {datetime.now().strftime("%Y-%m-%d")}
Method: Income Approach (DCF)
Valuation: {total_value/1e4:,.2f} 万元
Average NOI: {np.mean(nois)/1e4:,.2f} 万元
Terminal Value Share: {(1 - np.sum(pvs)/total_value)*100:.1f}%
""", align="L")
    pdf.add_page()

    # 图表页
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "NOI & PV Trend", ln=True, align="L")
    pdf.image(chart_buf, x=20, y=30, w=170)
    pdf_output = BytesIO(pdf.output(dest="S").encode("latin1"))

    st.download_button(
        T["export_pdf"],
        data=pdf_output,
        file_name=f"{project_name}_valuation_report.pdf",
        mime="application/pdf"
    )

