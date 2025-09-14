import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --- Page Configuration ---
st.set_page_config(
    page_title="Marketing Intelligence Dashboard",
    page_icon="📊",
    layout="wide"
)

# --- Data Loading and Preparation (Cached for performance) ---
@st.cache_data
def load_data():
    # Load all dataframes
    facebook = pd.read_csv('data/Facebook.csv')
    google = pd.read_csv('data/Google.csv')
    tiktok = pd.read_csv('data/TikTok.csv')
    business = pd.read_csv('data/Business.csv')

    # --- STANDARDIZE ALL COLUMNS ---
    for df_marketing in [facebook, google, tiktok]:
        df_marketing.columns = df_marketing.columns.str.lower().str.replace(' ', '_')
        if 'impression' in df_marketing.columns and 'impressions' not in df_marketing.columns:
            df_marketing.rename(columns={'impression': 'impressions'}, inplace=True)
        if 'attribute_revenue' in df_marketing.columns and 'attributed_revenue' not in df_marketing.columns:
            df_marketing.rename(columns={'attribute_revenue': 'attributed_revenue'}, inplace=True)

    business.columns = business.columns.str.lower().str.replace('# of ', '').str.replace(' ', '_')

    # Combine marketing data
    facebook['platform'] = 'Facebook'
    google['platform'] = 'Google'
    tiktok['platform'] = 'TikTok'
    marketing_data = pd.concat([facebook, google, tiktok], ignore_index=True)

    # Date conversion
    marketing_data['date'] = pd.to_datetime(marketing_data['date'])
    business['date'] = pd.to_datetime(business['date'])

    # Ensure numeric columns
    for col in ['spend', 'impressions', 'clicks', 'attributed_revenue']:
        if col not in marketing_data.columns:
            marketing_data[col] = 0
    marketing_data[['spend','impressions','clicks','attributed_revenue']] = marketing_data[['spend','impressions','clicks','attributed_revenue']].apply(pd.to_numeric, errors='coerce').fillna(0)

    # Aggregate for merging
    daily_marketing = marketing_data.groupby('date').agg({
        'spend':'sum','impressions':'sum','clicks':'sum','attributed_revenue':'sum'
    }).reset_index()

    # Merge with business data
    df = pd.merge(business, daily_marketing, on='date', how='left')
    df[['spend','impressions','clicks','attributed_revenue']] = df[['spend','impressions','clicks','attributed_revenue']].fillna(0)

    # Derived metrics
    epsilon = 1e-9
    df['roas'] = df['attributed_revenue'] / (df['spend'] + epsilon)
    df['mer'] = df['total_revenue'] / (df['spend'] + epsilon)
    df['cpc'] = df['spend'] / (df['clicks'] + epsilon)
    df['ctr'] = (df['clicks'] / (df['impressions'] + epsilon)) * 100
    if 'new_customers' not in df.columns:
        df['new_customers'] = 0
    df['cac'] = df['spend'] / (df['new_customers'] + epsilon)

    df.replace([float('inf'), -float('inf')], 0, inplace=True)
    df.fillna(0, inplace=True)

    return df, marketing_data

# --- Load data ---
df, marketing_data_raw = load_data()

# --- Sidebar ---
st.sidebar.header("Filters")
min_date, max_date = df['date'].min(), df['date'].max()
date_range = st.sidebar.date_input("Select Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

# --- Apply date filter ---
start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)].copy()
filtered_marketing = marketing_data_raw[(marketing_data_raw['date'] >= start_date) & (marketing_data_raw['date'] <= end_date)].copy()

# --- KPIs Section ---
st.title(" Marketing Intelligence Dashboard ")
st.header("Overall Performance")

total_revenue = filtered_df['total_revenue'].sum()
total_spend = filtered_df['spend'].sum()
total_profit = filtered_df['gross_profit'].sum() if 'gross_profit' in filtered_df.columns else 0
new_customers = filtered_df['new_customers'].sum()
overall_mer = total_revenue / (total_spend + 1e-9)
overall_cac = total_spend / (new_customers + 1e-9) if new_customers > 0 else 0
overall_ctr = (filtered_df['clicks'].sum() / (filtered_df['impressions'].sum() + 1e-9)) * 100

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Revenue", f"${total_revenue:,.0f}")
k2.metric("Total Ad Spend", f"${total_spend:,.0f}")
k3.metric("Gross Profit", f"${total_profit:,.0f}")
k4.metric("New Customers", f"{int(new_customers):,}")

k5, k6, _, _ = st.columns(4)
k5.metric("Marketing Efficiency Ratio (MER)", f"{overall_mer:.2f}")
k6.metric("Customer Acquisition Cost (CAC)", f"${overall_cac:.2f}")

# Quick Insights
st.subheader("Quick insights & recommendations")
insights = []
if overall_mer < 1:
    insights.append("MER < 1 — marketing is not driving positive top-line efficiency.")
if overall_ctr < 0.5:
    insights.append("CTR < 0.5% — check creative performance.")
if overall_cac > 50:
    insights.append("High CAC (> $50) — optimize ad spend or funnel.")
if not insights:
    insights.append("No immediate red flags detected.")
for out in insights:
    st.info(out)

# --- Trends ---
st.header("Performance Trends")
fig_trend = px.line(filtered_df, x='date', y=['total_revenue', 'spend'],
                    title="Total Revenue vs. Ad Spend Over Time")
st.plotly_chart(fig_trend, use_container_width=True)

if filtered_marketing.shape[0] > 0:
    daily_marketing_view = filtered_marketing.groupby('date', as_index=False).agg({
        'spend':'sum','impressions':'sum','clicks':'sum','attributed_revenue':'sum'
    })
    fig_m = px.line(daily_marketing_view, x='date', y=['spend','impressions','clicks','attributed_revenue'],
                    title="Marketing Metrics Over Time")
    st.plotly_chart(fig_m, use_container_width=True)

# --- Platform Performance ---
st.header("Platform Performance")
if filtered_marketing.shape[0] > 0:
    platform_perf = filtered_marketing.groupby('platform', as_index=False).agg({
        'spend':'sum','attributed_revenue':'sum','impressions':'sum','clicks':'sum'
    })
    platform_perf['roas'] = platform_perf['attributed_revenue'] / (platform_perf['spend'] + 1e-9)
    platform_perf['ctr'] = (platform_perf['clicks'] / (platform_perf['impressions'] + 1e-9)) * 100
    platform_perf = platform_perf.sort_values('roas', ascending=False)
    fig_roas = px.bar(platform_perf, x='platform', y='roas', text=platform_perf['roas'].round(2),
                      title="ROAS by Platform")
    st.plotly_chart(fig_roas, use_container_width=True)
    st.dataframe(platform_perf[['platform','spend','attributed_revenue','roas','ctr']].round(2))
else:
    st.warning("No marketing rows for selected date range.")

# --- Correlation Matrix ---
st.header("Correlation Matrix")
corr_cols = ['spend','impressions','clicks','attributed_revenue','total_revenue']
corr_exist = [c for c in corr_cols if c in filtered_df.columns]
if len(corr_exist) >= 2:
    corr_df = filtered_df[corr_exist].corr()
    fig_corr = px.imshow(corr_df, text_auto=True, title="Correlation matrix")
    st.plotly_chart(fig_corr, use_container_width=True)

# --- Daily Data Table ---
st.header("Daily Data View")
st.dataframe(filtered_df.reset_index(drop=True).round(2))

st.markdown("---")
st.caption("Use the date filter in the sidebar to explore trends over time.")
