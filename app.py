import streamlit as st
import os
import numpy as np
import pandas as pd
from fpdf import FPDF
from io import BytesIO
from datetime import datetime
import plotly.graph_objects as go

# ---------------- 页面配置 ----------------
st.set_page_config(
    page_title="REITs 收益法估值模型",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- 侧边栏导航 ----------------
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/5/50/REIT_logo_example.svg/512px-REIT_logo_example.svg.png",
             width=180)
    st.title("🏢 REITs估值SaaS")
    st.markdown("**版本：** 1.3.0  \n"
                "**作者：** 你的名字  \n"
                "**说明：** 基于收益法的资产估值工具，支持情景模拟和 PDF 报告导出。")
    st.divider()
    st.caption("© 2025 REITs Valuation Cloud")

# ---------------- 主标题区 ----------------
st.title("📈 保租房 REITs 收益法估值系统")
st.markdown("模拟收益法（Income Approach）下的底层资产估值，可自定义参数、生成报告。")

# ---------------- 参数输入区 ----------------
st.header("🧮 参数输入")
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
    term = st.number_input("收益期（年）", value=20, step=1)
    area = st.number_input("建筑面积（㎡）", value=53606.58, step=100.0)
    project_name = st.text_input("项目名称", value="安居百泉阁")

st.divider()
calculate = st.button("🚀 开始计算估值")

if calculate:
    # ---------------- 核心估值逻辑 ----------------
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

    # ---------------- 展示主要结果 ----------------
    st.success(f"✅ {project_name} 估值计算完成！")
    col1, col2, col3 = st.columns(3)
    col1.metric("资产估值（万元）", f"{total_value / 1e4:,.2f}")
    col2.metric("年度平均 NOI（万元）", f"{np.mean(nois)/1e4:,.2f}")
    col3.metric("终值贡献占比", f"{(tv / discount_factors[-1] / total_value)*100:.1f}%")

    # ---------------- 可视化图表 ----------------
    df = pd.DataFrame({"年份": years, "NOI": nois, "贴现现金流": pvs})
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years, y=nois, mode='lines+markers', name='NOI'))
    fig.add_trace(go.Scatter(x=years, y=pvs, mode='lines+markers', name='贴现现金流'))
    fig.update_layout(title="收益趋势与贴现现金流", xaxis_title="年份", yaxis_title="金额（元）")
    st.plotly_chart(fig, use_container_width=True)

    # ---------------- 数据表格 ----------------
    with st.expander("查看详细年度数据"):
        st.dataframe(df.style.format({"NOI": "{:,.0f}", "贴现现金流": "{:,.0f}"}))

    # ---------------- PDF 报告 ----------------
    pdf = FPDF()
    pdf.add_page()

    # 添加中文字体
    if not os.path.exists("NotoSansSC-Regular.ttf"):
        st.warning("⚠️ 缺少字体文件 NotoSansSC-Regular.ttf，请将其放置在项目根目录！")
    else:
        pdf.add_font("Noto", "", "NotoSansSC-Regular.ttf", uni=True)
        pdf.set_font("Noto", size=16)

        pdf.cell(0, 20, "REITs 收益法估值报告", ln=True, align="C")
        pdf.set_font("Noto", size=12)
        pdf.cell(0, 10, f"项目：{project_name}", ln=True)
        pdf.cell(0, 10, f"估值日期：{datetime.now().strftime('%Y-%m-%d')}", ln=True)
        pdf.cell(0, 10, f"估值结果：{total_value/1e4:,.2f} 万元", ln=True)
        pdf.cell(0, 10, f"折现率：{discount_rate*100:.2f}%", ln=True)
        pdf.cell(0, 10, f"长期增长率：{long_growth*100:.2f}%", ln=True)
        pdf.cell(0, 10, f"终值贡献：{(tv / discount_factors[-1] / total_value)*100:.1f}%", ln=True)
        pdf.ln(10)
        pdf.multi_cell(0, 10, "（图表部分请参考网页端展示）")

        pdf_output = BytesIO()
        pdf.output(pdf_output)
        st.download_button(
            label="📥 下载估值报告 PDF",
            data=pdf_output.getvalue(),
            file_name=f"{project_name}_估值报告.pdf",
            mime="application/pdf"
        )
else:
    st.info("👆 请填写参数后点击上方“开始计算估值”")

