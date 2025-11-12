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

# 多语言
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
    }
}

# 语言切换
lang_choice = st.sidebar.selectbox("🌐 Language / 语言", ["English", "中文"])
T = LANG["en" if lang_choice == "English" else "zh"]

# 标题
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
    term = st.number_input(T["term"], value=64)
    area = st.number_input(T["area"], value=53606.58)
    project_name = st.text_input(T["project"], value="安居百泉阁")

simulate = st.checkbox(T["simulate"], value=True)
delta = st.slider("变化幅度(%)", 1, 20, 5)

# 收益法函数
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

# 计算
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
    st.line_chart(df.set_index("Year"))

    # 图表生成
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot(df["Year"], df["NOI"], label="NOI", color="blue")
    ax.plot(df["Year"], df["PV"], label="PV", color="green")
    ax.legend()
    ax.set_title(T["chart"])
    chart_buf = BytesIO()
    plt.savefig(chart_buf, format="png")
    chart_buf.seek(0)

    # PDF 生成
    pdf = FPDF()
    pdf.add_page()

    # ✅ 加载中文字体（放在同目录）
    font_path = "NotoSansSC-Regular.ttf"  # 或 SimHei.ttf
    if os.path.exists(font_path):
        pdf.add_font("SimHei", "", font_path, uni=True)
        pdf.add_font("SimHei", "B", font_path, uni=True)  # ✅ 新增这行，注册粗体
        pdf.set_font("SimHei", "", 16)
    else:
        pdf.set_font("Arial", "", 16)

    pdf.cell(0, 10, "REITs 收益法估值报告", ln=True, align="C")

    logo_path = "logo.png"
    if os.path.exists(logo_path):
        pdf.image(logo_path, x=80, y=25, w=50)
    else:
        pdf.set_font("Arial", "I", 12)
        pdf.cell(0, 10, "(No logo found — add logo.png to project folder)", ln=True, align="C")

    pdf.ln(60)
    pdf.set_font("SimHei" if os.path.exists(font_path) else "Arial", "", 12)
    report_text = (
        f"项目名称：{project_name}\n"
        f"日期：{datetime.now().strftime('%Y-%m-%d')}\n"
        f"估值方法：收益法（DCF）\n"
        f"估值结果：{total_value/1e4:,.2f} 万元\n"
        f"平均 NOI：{np.mean(nois)/1e4:,.2f} 万元\n"
        f"终值贡献：{(1 - np.sum(pvs)/total_value)*100:.1f}%"
    )
    pdf.multi_cell(0, 10, report_text, align="L")

    # 图表页
    pdf.add_page()
    pdf.set_font("SimHei" if os.path.exists(font_path) else "Arial", "B", 14)
    pdf.cell(0, 10, T["chart"], ln=True)
    pdf.image(chart_buf, x=20, y=30, w=170)

    pdf_output = BytesIO(pdf.output(dest="S").encode("latin1"))
    st.download_button(T["export_pdf"], data=pdf_output,
                       file_name=f"{project_name}_valuation_report.pdf",
                       mime="application/pdf")

