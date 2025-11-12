import streamlit as st
import numpy as np
import pandas as pd
from io import BytesIO

# ---------------- 页面配置 ----------------
st.set_page_config(
    page_title="REITs Valuation SaaS",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- 多语言字典 ----------------
LANG = {
    "en": {
        "title": "🏢 REITs Valuation System (Income Approach)",
        "subtitle": "Simulate and compare property valuation results based on the Income Approach (DCF).",
        "input": "Parameter Settings",
        "calc": "🚀 Run Valuation",
        "scenario": "Scenario Simulation",
        "result": "Valuation Results",
        "avg_noi": "Average NOI (10k RMB)",
        "terminal": "Terminal Value Share",
        "project": "Project Name",
        "detail": "Show Detailed Data",
        "report": "Valuation Summary Report",
        "export_excel": "📤 Export as Excel",
        "export_pdf": "🧾 Export as PDF",
        "base_rent": "Base Rent (RMB/m²/month)",
        "rent_growth": "Rent Growth Rate (%)",
        "occupancy": "Occupancy (%)",
        "cost_ratio": "Operating Cost Ratio (%)",
        "discount_rate": "Discount Rate (%)",
        "long_growth": "Terminal Growth Rate (%)",
        "term": "Valuation Period (years)",
        "area": "Gross Floor Area (m²)",
        "simulate": "Scenario Simulation (± changes)",
        "scenario_chart": "Scenario Valuation Comparison"
    },
    "zh": {
        "title": "🏢 REITs 收益法估值系统",
        "subtitle": "基于收益法（DCF）的房地产估值模型，可进行多情景模拟和结果导出。",
        "input": "参数输入",
        "calc": "🚀 开始计算估值",
        "scenario": "情景模拟",
        "result": "估值结果",
        "avg_noi": "平均年度 NOI（万元）",
        "terminal": "终值贡献占比",
        "project": "项目名称",
        "detail": "查看年度数据",
        "report": "估值报告摘要",
        "export_excel": "📤 导出 Excel 报告",
        "export_pdf": "🧾 导出 PDF 报告",
        "base_rent": "起始租金（元/㎡/月）",
        "rent_growth": "租金年增长率（%）",
        "occupancy": "出租率（%）",
        "cost_ratio": "运营成本率（%）",
        "discount_rate": "折现率（%）",
        "long_growth": "永续增长率（%）",
        "term": "收益期（年）",
        "area": "建筑面积（㎡）",
        "simulate": "情景模拟（参数 ± 变化）",
        "scenario_chart": "情景估值对比"
    }
}

# ---------------- 语言选择 ----------------
lang_choice = st.sidebar.selectbox("🌐 Language / 语言", ["English", "中文"])
LANG_SEL = "en" if lang_choice == "English" else "zh"
T = LANG[LANG_SEL]

# ---------------- 页面标题 ----------------
st.title(T["title"])
st.markdown(T["subtitle"])
st.divider()

# ---------------- 参数输入 ----------------
st.header(f"🧮 {T['input']}")

col1, col2, col3 = st.columns(3)
with col1:
    base_rent = st.number_input(T["base_rent"], value=60.73, step=1.0)
    occupancy = st.number_input(T["occupancy"], value=98.0, step=0.1) / 100
    cost_ratio = st.number_input(T["cost_ratio"], value=15.5, step=0.1) / 100
with col2:
    rent_growth = st.number_input(T["rent_growth"], value=0.67, step=0.1) / 100
    discount_rate = st.number_input(T["discount_rate"], value=6.0, step=0.1) / 100
    long_growth = st.number_input(T["long_growth"], value=2.5, step=0.1) / 100
with col3:
    term = st.number_input(T["term"], value=64, step=1)
    area = st.number_input(T["area"], value=53606.58, step=100.0)
    project_name = st.text_input(T["project"], value="安居百泉阁")

st.divider()

# ---------------- 情景模拟设置 ----------------
st.subheader(f"🧩 {T['scenario']}")
scenario_enable = st.checkbox(f"{T['simulate']}", value=True)
delta = st.slider("参数变化幅度 (%)", 1, 20, 5)

# ---------------- 估值函数 ----------------
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

# ---------------- 执行计算 ----------------
if st.button(T["calc"]):
    nois, pvs, total_value = income_valuation(
        base_rent, rent_growth, occupancy, cost_ratio,
        discount_rate, long_growth, term, area
    )

    st.success(f"✅ {T['result']}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Valuation (10k RMB)", f"{total_value / 1e4:,.2f}")
    col2.metric(T["avg_noi"], f"{np.mean(nois)/1e4:,.2f}")
    col3.metric(T["terminal"], f"{(1 - np.sum(pvs)/total_value)*100:.1f}%")

    df = pd.DataFrame({
        "Year": np.arange(1, int(term) + 1),
        "NOI": nois,
        "PV": pvs
    })
    st.line_chart(df.set_index("Year"))

    with st.expander(T["detail"]):
        st.dataframe(df.style.format({"NOI": "{:,.0f}", "PV": "{:,.0f}"}))

    # ---------------- 导出 Excel 报告 ----------------
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="ValuationData", index=False)
        summary = pd.DataFrame({
            "Metric": ["Valuation", "Avg NOI", "Terminal Share"],
            "Value": [total_value/1e4, np.mean(nois)/1e4, (1 - np.sum(pvs)/total_value)*100]
        })
        summary.to_excel(writer, sheet_name="Summary", index=False)
    output.seek(0)

    st.download_button(
        label=T["export_excel"],
        data=output,
        file_name=f"{project_name}_valuation.xlsx",
        mime="application/vnd.ms-excel"
    )

    # ---------------- 情景模拟 ----------------
    if scenario_enable:
        st.divider()
        st.subheader(f"📊 {T['scenario_chart']}")
        scenarios = {
            "Base": [base_rent, rent_growth, occupancy, cost_ratio, discount_rate, long_growth],
            "+Δ": [
                base_rent*(1+delta/100),
                rent_growth*(1+delta/100),
                occupancy*(1+delta/100),
                cost_ratio,
                discount_rate*(1-delta/100),
                long_growth*(1+delta/100)
            ],
            "-Δ": [
                base_rent*(1-delta/100),
                rent_growth*(1-delta/100),
                occupancy*(1-delta/100),
                cost_ratio,
                discount_rate*(1+delta/100),
                long_growth*(1-delta/100)
            ]
        }
        values = []
        for key, vals in scenarios.items():
            nois_s, pvs_s, val = income_valuation(*vals, term, area)
            values.append(val/1e4)
        sim_df = pd.DataFrame({
            "Scenario": ["-Δ", "Base", "+Δ"],
            "Valuation (10k RMB)": values[::-1]
        }).set_index("Scenario")
        st.bar_chart(sim_df)
