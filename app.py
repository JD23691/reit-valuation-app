import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
from datetime import datetime
from io import BytesIO

# ===================== 页面配置 =====================
st.set_page_config(page_title="REITs 收益法估值系统", layout="wide")

# ===================== 侧边栏 =====================
with st.sidebar:
    st.image("logo.png", width=300)
    st.title("REITs估值终端")
    st.markdown("**版本：** 3.1.0\n\n**作者：** 你的名字\n\n**说明：** 专业化REITs底层资产收益法估值与报告生成工具。")
    st.divider()
    st.caption("© 2025 REITs Valuation Cloud")

# ===================== 主标题 =====================
st.title("保租房 REITs 收益法估值系统")
st.markdown("通过收益法（Income Approach）计算保租房底层资产估值，并生成专业 PDF 报告。")

# ===================== 参数输入区 =====================
st.header("参数输入")

col1, col2, col3 = st.columns(3)
with col1:
    base_rent = st.number_input("起始租金（元/㎡/月）", value=60.73, step=1.0)
    occupancy = st.number_input("出租率（%）", value=98.0, step=0.1) / 100
    cost_ratio = st.number_input("运营成本率（%）", value=15.5, step=0.1) / 100
with col2:
    rent_growth = st.number_input("租金年增长率（%）", value=0.67, step=0.1) / 100
    discount_rate = st.number_input("折现率（%）", value=6.0, step=0.1) / 100
    long_growth = st.number_input("永续增长率（%）", value=2.5, step=0.1) / 100
with col3:
    term = st.number_input("收益期（年）", value=64, step=1)
    area = st.number_input("建筑面积（㎡）", value=53606.58, step=100.0)
    project_name = st.text_input("项目名称", value="安居百泉阁")

delta = st.slider("情景变化幅度（±%）", 1, 20, 5)
company_name = st.text_input("估值机构名称", value="中信资管估值部")

st.divider()


# ===================== 收益法函数 =====================
def income_valuation(base_rent, rent_growth, occupancy, cost_ratio,
                     discount_rate, long_growth, term, area):
    nois, rents = [], []
    for t in range(1, int(term) + 1):
        rent_t = base_rent * ((1 + rent_growth) ** t) * occupancy * area * 12
        cost_t = rent_t * cost_ratio
        noi_t = rent_t - cost_t
        rents.append(rent_t)
        nois.append(noi_t)
    tv = nois[-1] * (1 + long_growth) / (discount_rate - long_growth)
    years = np.arange(1, int(term) + 1)
    discount_factors = (1 + discount_rate) ** years
    pvs = np.array(nois) / discount_factors
    total_value = np.sum(pvs) + tv / discount_factors[-1]
    return nois, pvs, total_value, tv, discount_factors


# ===================== 计算按钮 =====================
calculate = st.button("开始计算估值")

if calculate:

    # -------- 核心计算 --------
    nois, pvs, total_value, tv, discount_factors = income_valuation(
        base_rent, rent_growth, occupancy, cost_ratio,
        discount_rate, long_growth, term, area
    )

    st.success("计算完成！")

    # -------- 结果展示 --------
    col1, col2, col3 = st.columns(3)
    col1.metric("资产估值（万元）", f"{total_value / 1e4:,.2f}")
    col2.metric("年度平均 NOI（万元）", f"{np.mean(nois)/1e4:,.2f}")
    col3.metric("终值贡献占比", f"{(tv / discount_factors[-1] / total_value)*100:.1f}%")

    # -------- Plotly 图表 --------
    df = pd.DataFrame({
        "年份": np.arange(1, int(term) + 1),
        "NOI": nois,
        "贴现现金流": pvs
    })

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["年份"], y=df["NOI"], mode="lines", name="NOI",
                             line=dict(color="#0052CC", width=3)))
    fig.add_trace(go.Scatter(x=df["年份"], y=df["贴现现金流"], mode="lines", name="贴现现金流",
                             line=dict(color="#00A86B", width=3)))

    fig.update_layout(
        title="📊 收益趋势与贴现现金流",
        template="plotly_white",
        xaxis_title="年份",
        yaxis_title="金额 (元)",
        legend_title="指标"
    )

    st.plotly_chart(fig, use_container_width=True)

    # -------- 情景分析 --------
    st.subheader("情景估值模拟")

    scenarios = {
        "基准情景": [base_rent, rent_growth, occupancy, cost_ratio, discount_rate, long_growth],
        "乐观情景": [base_rent*(1+delta/100), rent_growth*(1+delta/100),
                     occupancy*(1+delta/100), cost_ratio, discount_rate*(1-delta/100),
                     long_growth*(1+delta/100)],
        "悲观情景": [base_rent*(1-delta/100), rent_growth*(1-delta/100),
                     occupancy*(1-delta/100), cost_ratio, discount_rate*(1+delta/100),
                     long_growth*(1-delta/100)]
    }

    results = {}
    for s, vals in scenarios.items():
        _, _, v, _, _ = income_valuation(*vals, term, area)
        results[s] = v / 1e4

    df_s = pd.DataFrame.from_dict(results, orient="index", columns=["估值（万元）"])
    st.bar_chart(df_s)

    # ===================== PDF 报告生成 =====================

    pdf = FPDF()
    pdf.add_page()

    # ➤ 注册中文字体
    pdf.add_font("NotoSans", "", "NotoSansSC-Regular.ttf", uni=True)
    pdf.set_font("NotoSans", size=20)

    # -------- 封面页 --------
    pdf.cell(0, 20, "REITs 收益法估值报告", ln=True, align="C")
    pdf.ln(15)

    pdf.set_font("NotoSans", size=12)
    pdf.multi_cell(0, 10, f"""
项目名称：{project_name}
估值机构：{company_name}
估值日期：{datetime.now().strftime('%Y-%m-%d')}
估值方法：收益法 (Discounted Cash Flow)
""")

    # -------- 第二页：估值摘要 --------
    pdf.add_page()
    pdf.set_font("NotoSans", size=16)
    pdf.cell(0, 10, "一、估值结果摘要", ln=True)
    pdf.ln(4)

    pdf.set_font("NotoSans", size=12)
    pdf.multi_cell(0, 10, f"""
资产估值：{total_value/1e4:,.2f} 万元
平均 NOI：{np.mean(nois)/1e4:,.2f} 万元
折现率：{discount_rate*100:.2f}%
长期增长率：{long_growth*100:.2f}%
收益期：{int(term)} 年
终值贡献：{(tv / discount_factors[-1] / total_value)*100:.1f}%

说明：图表请参见 Web 端动态展示（支持缩放、悬停显示）。
""")

    # -------- 第三页：情景分析 --------
    pdf.add_page()
    pdf.set_font("NotoSans", size=16)
    pdf.cell(0, 10, "二、情景估值模拟", ln=True)
    pdf.ln(5)

    pdf.set_font("NotoSans", size=12)
    for s, v in results.items():
        pdf.cell(0, 10, f"{s}：{v:,.2f} 万元", ln=True)

    pdf.ln(10)
    pdf.cell(0, 10, f"变化幅度设定：±{delta}%", ln=True)

    pdf.set_y(-15)
    pdf.set_font("NotoSans", size=10)
    pdf.cell(0, 10, f"© {datetime.now().year} {company_name} 保留所有权利", align="C")

    # -------- 导出 PDF --------
    pdf_output = BytesIO(pdf.output(dest="S"))
    st.download_button(
        "🧾 导出完整 PDF 报告",
        data=pdf_output,
        file_name=f"{project_name}_估值报告.pdf",
        mime="application/pdf"
    )

else:
    st.info("请在上方填写参数后点击“开始计算估值”。")
