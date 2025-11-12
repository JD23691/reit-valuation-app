import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO
from datetime import datetime
import os

# 页面设置
st.set_page_config(page_title="REITs Valuation SaaS", page_icon="🏢", layout="wide")

# ================= 多语言 ==================
LANG = {
    "en": {
        "title": "🏢 REITs Valuation System (Income Approach)",
        "subtitle": "Professional REIT valuation with DCF and scenario simulation.",
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
        "company": "Company Name",
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
        "company": "估值机构名称",
        "scenario_chart": "情景估值对比"
    }
}

# 语言切换
lang_choice = st.sidebar.selectbox("🌐 Language / 语言", ["English", "中文"])
T = LANG["en" if lang_choice == "English" else "zh"]

# ================= 页面布局 ==================
st.title(T["title"])
st.caption(T["subtitle"])
st.divider()

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
    term = st.number_input(T["term"], value=64)
    area = st.number_input(T["area"], value=53606.58)
    project_name = st.text_input(T["project"], value="安居百泉阁")

simulate = st.checkbox(T["simulate"], value=True)
delta = st.slider("变化幅度(%)", 1, 20, 5)
company_name = st.text_input(T["company"], value="中信资管估值部")

# ================= 收益法计算 ==================
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

# ================= 主逻辑 ==================
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

    df = pd.DataFrame({"Year": np.arange(1, int(term) + 1), "NOI": nois, "PV": pvs})

    # ======== 使用原版更漂亮的图表 ========
    chart_buf = BytesIO()
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(df["Year"], df["NOI"], label="NOI（净经营收益）", color="#0052CC", linewidth=2.5)
    ax.plot(df["Year"], df["PV"], label="PV（贴现现金流）", color="#00A86B", linewidth=2.5)
    ax.fill_between(df["Year"], df["PV"], color="#00A86B", alpha=0.15)
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend(frameon=False, fontsize=10)
    ax.set_title(T["chart"], fontsize=14, fontweight="bold", pad=10)
    ax.set_xlabel("Year")
    ax.set_ylabel("Value (RMB)")
    plt.tight_layout()
    st.pyplot(fig)

    # 保存相同图表
    plt.savefig(chart_buf, format="png", bbox_inches="tight")
    chart_buf.seek(0)
    plt.close(fig)

    # ============ PDF 报告生成 ==============
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # ✅ 字体加载（支持中文 + 粗体）
    font_path = "NotoSansSC-Regular.ttf"
    if os.path.exists(font_path):
        for style in ["", "B"]:
            pdf.add_font("SimHei", style, font_path, uni=True)
        pdf.set_font("SimHei", "B", 20)
    else:
        pdf.set_font("Arial", "B", 20)

    # 封面
    pdf.cell(0, 15, "REITs 收益法估值报告", ln=True, align="C")
    pdf.ln(10)
    if os.path.exists("logo.png"):
        pdf.image("logo.png", x=80, y=35, w=50)
    pdf.ln(70)
    pdf.set_font("SimHei" if os.path.exists(font_path) else "Arial", "", 13)
    pdf.cell(0, 10, f"项目名称：{project_name}", ln=True, align="C")
    pdf.cell(0, 10, f"估值机构：{company_name}", ln=True, align="C")
    pdf.cell(0, 10, f"估值日期：{datetime.now().strftime('%Y-%m-%d')}", ln=True, align="C")
    pdf.cell(0, 10, f"估值结果：{total_value/1e4:,.2f} 万元", ln=True, align="C")

    # 第二页：图表页
    pdf.add_page()
    pdf.set_font("SimHei", "B", 16)
    pdf.cell(0, 10, T["chart"], ln=True)
    pdf.image(chart_buf, x=15, y=30, w=180)

    # 页脚
    pdf.set_y(-15)
    pdf.set_font("SimHei", "", 10)
    pdf.cell(0, 10, f"© {datetime.now().year} {company_name} 保留所有权利", align="C")

    # 输出 PDF
    pdf_output = BytesIO(pdf.output(dest="S"))
    st.download_button(
        T["export_pdf"],
        data=pdf_output,
        file_name=f"{project_name}_valuation_report.pdf",
        mime="application/pdf"
    )
