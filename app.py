import streamlit as st
import numpy as np

st.set_page_config(page_title="REITs 收益法估值模型", layout="centered")

st.title("🏢 REITs 收益法估值模型（网页版）")
st.markdown("输入参数后点击下方按钮，即可计算估值结果。")

# 参数输入
base_rent = st.number_input("起始租金（元/㎡/月）", value=60.73)
rent_growth = st.number_input("租金年增长率（%）", value=0.67) / 100
occupancy = st.number_input("出租率（%）", value=98.0) / 100
cost_ratio = st.number_input("运营成本率（%）", value=15.5) / 100
discount_rate = st.number_input("折现率（%）", value=6.0) / 100
long_growth = st.number_input("永续增长率（%）", value=2.5) / 100
term = st.number_input("收益年限（年）", value=64, step=1)
area = st.number_input("建筑面积（㎡）", value=53606.58)

if st.button("计算估值"):
    nois = []
    for t in range(1, int(term) + 1):
        rent_t = base_rent * ((1 + rent_growth) ** t) * occupancy * area * 12
        cost_t = rent_t * cost_ratio
        noi_t = rent_t - cost_t
        nois.append(noi_t)

    tv = nois[-1] * (1 + long_growth) / (discount_rate - long_growth)
    years = np.arange(1, int(term) + 1)
    discount_factors = (1 + discount_rate) ** years
    pvs = np.array(nois) / discount_factors
    total_value = np.sum(pvs) + tv / discount_factors[-1]

    st.success(f"💰 项目估值：{total_value / 1e4:,.2f} 万元")
    st.write(f"年度平均 NOI：{np.mean(nois)/1e4:,.2f} 万元")
    st.line_chart(nois)
