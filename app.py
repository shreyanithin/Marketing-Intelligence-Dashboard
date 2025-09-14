import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Page Configuration
st.set_page_config(
    page_title="Marketing Intelligence Dashboard",
    page_icon="🚀",
    layout="wide"
)

# Data Loading and Preparation
@st.cache_data
def load_data():
    # Load all dataframes
    facebook = pd.read_csv('data/Facebook.csv')
    google = pd.read_csv('data/Google.csv')
    tiktok = pd.read_csv('data/TikTok.csv')
    business = pd.read_csv('data/Business.csv')

    # STANDARDIZE ALL COLUMNS AT THE START
    for df_marketing in [facebook, google, tiktok]:
        df_marketing.columns = df_marketing.columns.str.lower().str.replace(' ', '_')
        if 'impression' in df_marketing.columns and 'impressions' not in df_marketing.columns:
            df_marketing.rename(columns={'impression': 'impressions'}, inplace=True)
    business.columns = business.columns.str.lower().str.replace('# of ', '').str.replace(' ', '_')

    # PREPARATION AND MERGING
    facebook['platform'] = 'Facebook'
    google['platform'] = 'Google'
    tiktok['platform'] = 'TikTok'
    marketing_data = pd.concat([facebook, google, tiktok], ignore_index=True)
    marketing_data['date'] = pd.to_datetime(marketing_data['date'])
    business['date'] = pd.to_datetime(business['date'])

    daily_marketing = marketing_data.groupby('date').agg({
        'spend': 'sum', 'impressions': 'sum', 'clicks': 'sum', 'attributed_revenue': 'sum'
    }).reset_index()

    df = pd.merge(business, daily_marketing, on='date', how='left').fillna(0)

    # FEATURE ENGINEERING
    epsilon = 1e-9
    df['roas'] = df['attributed_revenue'] / (df['spend'] + epsilon)
    df['mer'] = df['total_revenue'] / (df['spend'] + epsilon)
    df['cpc'] = df['spend'] / (df['clicks'] + epsilon)
    df['ctr'] = (df['clicks'] / (df['impressions'] + epsilon)) * 100
    df['cac'] = df['spend'] / (df['new_customers'] + epsilon)
    df.replace([np.inf, -np.inf], 0, inplace=True)
    df.fillna(0, inplace=True)

    return df, marketing_data

# Load data
df, marketing_data_raw = load_data()

# Professional Plotly Template 
THEME = "plotly_white"

# Sidebar Filters
with st.sidebar:
    st.header("Dashboard Filters")
    min_date, max_date = df['date'].min(), df['date'].max()
    date_range = st.date_input("Select Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

    platforms = sorted(marketing_data_raw['platform'].unique().tolist())
    states = sorted(marketing_data_raw['state'].unique().tolist())
    tactics = sorted(marketing_data_raw['tactic'].unique().tolist())

    selected_platforms = st.multiselect("Platforms", options=platforms, default=platforms)
    selected_states = st.multiselect("States", options=states, default=states)
    selected_tactics = st.multiselect("Tactics", options=tactics, default=tactics)

# Apply filters
start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
mask_marketing = (
    (marketing_data_raw['date'] >= start_date) & (marketing_data_raw['date'] <= end_date) &
    (marketing_data_raw['platform'].isin(selected_platforms)) &
    (marketing_data_raw['state'].isin(selected_states)) &
    (marketing_data_raw['tactic'].isin(selected_tactics))
)
filtered_marketing = marketing_data_raw[mask_marketing].copy()
filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)].copy()

#  Dashboard UI
st.markdown("<h1 style='text-align: center; font-size: 52px;'> Marketing Intelligence Dashboard</h1>", unsafe_allow_html=True)
st.markdown("---")

# KPIs Section
filtered_spend = filtered_marketing['spend'].sum()
total_revenue = filtered_df['total_revenue'].sum()
total_profit = filtered_df['gross_profit'].sum()
new_customers = filtered_df['new_customers'].sum()
overall_mer = total_revenue / filtered_spend if filtered_spend > 0 else 0
overall_cac = filtered_spend / new_customers if new_customers > 0 else 0

st.header(" Overall Performance")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"${total_revenue:,.0f}")
col2.metric("Filtered Ad Spend", f"${filtered_spend:,.0f}")
col3.metric("Gross Profit", f"${total_profit:,.0f}")
col4.metric("New Customers", f"{int(new_customers):,}")
st.write("") 

col5, col6, _, _ = st.columns(4)
col5.metric("Marketing Efficiency (MER)", f"{overall_mer:.2f}")
col6.metric("Customer Acquisition Cost (CAC)", f"${overall_cac:.2f}")
st.markdown("---")

# Insights & Recommendations
st.header(" Insights & Recommendations")
if not filtered_marketing.empty and 'campaign' in filtered_marketing.columns:
    platform_perf = filtered_marketing.groupby('platform').agg(attributed_revenue=('attributed_revenue', 'sum'), spend=('spend', 'sum')).reset_index()
    platform_perf['roas'] = platform_perf['attributed_revenue'] / (platform_perf['spend'] + 1e-9)
    best_platform = platform_perf.loc[platform_perf['roas'].idxmax()]

    tactic_perf = filtered_marketing.groupby('tactic').agg(attributed_revenue=('attributed_revenue', 'sum'), spend=('spend', 'sum')).reset_index()
    tactic_perf['roas'] = tactic_perf['attributed_revenue'] / (tactic_perf['spend'] + 1e-9)
    best_tactic = tactic_perf.loc[tactic_perf['roas'].idxmax()]

    campaigns = filtered_marketing.groupby('campaign').agg(spend=('spend', 'sum'), attributed_revenue=('attributed_revenue', 'sum')).reset_index()
    campaigns['roas'] = campaigns['attributed_revenue'] / (campaigns['spend'] + 1e-9)

    high_roas_threshold = campaigns['roas'].quantile(0.90)
    low_spend_threshold = campaigns['spend'].quantile(0.50)
    high_spend_threshold = campaigns['spend'].quantile(0.90)
    opportunity_df = campaigns[(campaigns['roas'] >= high_roas_threshold) & (campaigns['spend'] <= low_spend_threshold) & (campaigns['spend'] > 0)]
    opportunity_campaign = opportunity_df.sort_values('roas', ascending=False).iloc[0] if not opportunity_df.empty else None
    review_df = campaigns[(campaigns['spend'] >= high_spend_threshold) & (campaigns['roas'] < 1.2)]
    review_campaign = review_df.sort_values('spend', ascending=False).iloc[0] if not review_df.empty else None

    insight_cols = st.columns(3)
    with insight_cols[0]:
        st.info(f"**Top Performer:** {best_platform['platform']} is the most efficient platform (ROAS: {best_platform['roas']:.2f}).")
    with insight_cols[1]:
        if opportunity_campaign is not None:
            st.success(f"**Opportunity:** '{opportunity_campaign['campaign']}' has high ROAS ({opportunity_campaign['roas']:.2f}) on low spend (${opportunity_campaign['spend']:,.0f}). Consider scaling.")
    with insight_cols[2]:
        if review_campaign is not None:
            st.warning(f"**Area for Review:** '{review_campaign['campaign']}' has high spend (${review_campaign['spend']:,.0f}) but low ROAS ({review_campaign['roas']:.2f}).")
else:
    st.info("Not enough data with the current filters to generate insights.")
st.markdown("---")

# Performance Trends
st.header(" Performance Over Time")
fig_trend = px.line(filtered_df, x='date', y=['total_revenue', 'gross_profit'], title="Revenue and Profit Over Time", template=THEME)
fig_trend.update_layout(legend_title_text='Metric', yaxis_title='Amount ($)')
st.plotly_chart(fig_trend, use_container_width=True)
st.markdown("---")

# Channel & Tactic Performance
st.header(" Channel & Tactic Breakdown")
col_plat, col_tac = st.columns(2)
with col_plat:
    if not filtered_marketing.empty:
        platform_perf = filtered_marketing.groupby('platform').agg(spend=('spend', 'sum'), attributed_revenue=('attributed_revenue', 'sum')).reset_index()
        platform_perf['roas'] = platform_perf['attributed_revenue'] / platform_perf['spend']
        fig_roas = px.bar(platform_perf.sort_values('roas', ascending=True), x='roas', y='platform', orientation='h', title="ROAS by Platform", text=platform_perf['roas'].round(2), template=THEME)
        st.plotly_chart(fig_roas, use_container_width=True)
with col_tac:
    if not filtered_marketing.empty:
        tactic_perf = filtered_marketing.groupby('tactic').agg(spend=('spend', 'sum'), attributed_revenue=('attributed_revenue', 'sum')).reset_index()
        tactic_perf['roas'] = tactic_perf['attributed_revenue'] / tactic_perf['spend']
        fig_tactic = px.bar(tactic_perf.sort_values('roas', ascending=True), x='roas', y='tactic', orientation='h', title="ROAS by Tactic", text=tactic_perf['roas'].round(2), template=THEME)
        st.plotly_chart(fig_tactic, use_container_width=True)
st.markdown("---")

# Geographic & Campaign Performance
st.header(" Geographic & Campaign Deep Dive")
col_state, col_camp = st.columns(2)
with col_state:
    st.subheader("Performance by State")
    if not filtered_marketing.empty:
        state_perf = filtered_marketing.groupby('state').agg(spend=('spend', 'sum'), attributed_revenue=('attributed_revenue', 'sum')).reset_index()
        state_perf['roas'] = state_perf['attributed_revenue'] / state_perf['spend']
        fig_state = px.bar(state_perf.sort_values('spend', ascending=False).head(10), x='state', y='spend', color='roas', title="Top 10 States by Spend (Color = ROAS)", hover_data=['roas', 'attributed_revenue'], template=THEME)
        st.plotly_chart(fig_state, use_container_width=True)
with col_camp:
    st.subheader("Campaign Efficiency")
    if not filtered_marketing.empty:
        campaigns = filtered_marketing.groupby(['campaign', 'tactic']).agg(spend=('spend', 'sum'), attributed_revenue=('attributed_revenue', 'sum'), impressions=('impressions', 'sum')).reset_index()
        campaigns['roas'] = campaigns['attributed_revenue'] / (campaigns['spend'] + 1e-9)
        fig_scatter = px.scatter(campaigns, x='spend', y='roas', size='impressions', color='tactic', hover_data=['campaign', 'tactic'], title='Spend vs. ROAS (Color = Tactic)', labels={'spend': 'Total Spend ($)', 'roas': 'Return on Ad Spend'}, template=THEME)
        st.plotly_chart(fig_scatter, use_container_width=True)

# Data Table Expander 
with st.expander("Show Detailed Daily Data"):
    st.dataframe(filtered_df.reset_index(drop=True).round(2))