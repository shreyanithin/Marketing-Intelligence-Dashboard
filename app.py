import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

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

    # Clean marketing data columns
    for df_marketing in [facebook, google, tiktok]:
        df_marketing.columns = df_marketing.columns.str.lower().str.replace(' ', '_')
        if 'impression' in df_marketing.columns and 'impressions' not in df_marketing.columns:
            df_marketing.rename(columns={'impression': 'impressions'}, inplace=True)

    # Clean business data columns
    business.columns = business.columns.str.lower().str.replace('# of ', '').str.replace(' ', '_')

    # --- PREPARATION AND MERGING ---
    # Add platform identifiers and combine marketing data
    facebook['platform'] = 'Facebook'
    google['platform'] = 'Google'
    tiktok['platform'] = 'TikTok'
    marketing_data = pd.concat([facebook, google, tiktok], ignore_index=True)

    # Convert date columns to datetime
    marketing_data['date'] = pd.to_datetime(marketing_data['date'])
    business['date'] = pd.to_datetime(business['date'])

    # Aggregate marketing data for joining with business data
    daily_marketing = marketing_data.groupby('date').agg({
        'spend': 'sum',
        'impressions': 'sum',
        'clicks': 'sum',
        'attributed_revenue': 'sum'
    }).reset_index()

    # Join marketing and business data
    df = pd.merge(business, daily_marketing, on='date', how='left').fillna(0)

    # --- FEATURE ENGINEERING (Calculate Key Metrics) ---
    epsilon = 1e-9  # Use a small number to avoid division by zero
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

# --- Sidebar Filters ---
st.sidebar.header("Dashboard Filters")
min_date, max_date = df['date'].min(), df['date'].max()
date_range = st.sidebar.date_input("Select Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

# Get unique values for filters from the raw marketing data
platforms = sorted(marketing_data_raw['platform'].unique().tolist())
states = sorted(marketing_data_raw['state'].unique().tolist())
tactics = sorted(marketing_data_raw['tactic'].unique().tolist())

selected_platforms = st.sidebar.multiselect("Platforms", options=platforms, default=platforms)
selected_states = st.sidebar.multiselect("States", options=states, default=states)
selected_tactics = st.sidebar.multiselect("Tactics", options=tactics, default=tactics)

# --- Apply filters to dataframes ---
start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])

# Filter the raw marketing data based on all sidebar selections
mask_marketing = (
    (marketing_data_raw['date'] >= start_date) &
    (marketing_data_raw['date'] <= end_date) &
    (marketing_data_raw['platform'].isin(selected_platforms)) &
    (marketing_data_raw['state'].isin(selected_states)) &
    (marketing_data_raw['tactic'].isin(selected_tactics))
)
filtered_marketing = marketing_data_raw[mask_marketing].copy()

# The main `df` only needs to be filtered by date for business-wide KPIs
filtered_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)].copy()

# --- Dashboard UI ---
st.title(" Marketing Intelligence Dashboard")

# --- KPIs Section ---
st.header("Overall Performance")

# Recalculate spend based on filtered marketing data for accurate MER/CAC
filtered_spend = filtered_marketing['spend'].sum()
total_revenue = filtered_df['total_revenue'].sum()
total_profit = filtered_df['gross_profit'].sum()
new_customers = filtered_df['new_customers'].sum()

# Calculate metrics safely
overall_mer = total_revenue / filtered_spend if filtered_spend > 0 else 0
overall_cac = filtered_spend / new_customers if new_customers > 0 else 0

# Display KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"${total_revenue:,.0f}")
col2.metric("Filtered Ad Spend", f"${filtered_spend:,.0f}")
col3.metric("Gross Profit", f"${total_profit:,.0f}")
col4.metric("New Customers", f"{int(new_customers):,}")

col5, col6, _, _ = st.columns(4)
col5.metric("Marketing Efficiency Ratio (MER)", f"{overall_mer:.2f}")
col6.metric("Customer Acquisition Cost (CAC)", f"${overall_cac:.2f}")

# --- Performance Trends ---
st.header("Performance Trends")
fig_trend = px.line(filtered_df, x='date', y=['total_revenue', 'gross_profit'],
                    title="Revenue and Profit Over Time",
                    labels={'value': 'Amount ($)', 'variable': 'Metric'})
st.plotly_chart(fig_trend, use_container_width=True)

st.markdown("---")

# --- Channel & Tactic Performance ---
st.header("Channel & Tactic Performance")
col_plat, col_tac = st.columns(2)

with col_plat:
    if not filtered_marketing.empty:
        platform_perf = filtered_marketing.groupby('platform').agg(
            spend=('spend', 'sum'),
            attributed_revenue=('attributed_revenue', 'sum')
        ).reset_index()
        platform_perf['roas'] = platform_perf['attributed_revenue'] / platform_perf['spend']
        platform_perf = platform_perf.sort_values('roas', ascending=True)

        fig_roas = px.bar(platform_perf, x='roas', y='platform', orientation='h',
                          title="Return On Ad Spend (ROAS) by Platform",
                          text=platform_perf['roas'].round(2))
        st.plotly_chart(fig_roas, use_container_width=True)
    else:
        st.warning("No data for selected platform filters.")

with col_tac:
    if not filtered_marketing.empty:
        tactic_perf = filtered_marketing.groupby('tactic').agg(
            spend=('spend', 'sum'),
            attributed_revenue=('attributed_revenue', 'sum')
        ).reset_index()
        tactic_perf['roas'] = tactic_perf['attributed_revenue'] / tactic_perf['spend']
        tactic_perf = tactic_perf.sort_values('roas', ascending=True)

        fig_tactic = px.bar(tactic_perf, x='roas', y='tactic', orientation='h',
                            title="ROAS by Tactic",
                            text=tactic_perf['roas'].round(2))
        st.plotly_chart(fig_tactic, use_container_width=True)
    else:
        st.warning("No data for selected tactic filters.")

st.markdown("---")

# --- Geographic & Campaign Performance ---
st.header("Geographic & Campaign Deep Dive")
col_state, col_camp = st.columns(2)

with col_state:
    st.subheader("Performance by State")
    if not filtered_marketing.empty:
        state_perf = filtered_marketing.groupby('state').agg(
            spend=('spend', 'sum'),
            attributed_revenue=('attributed_revenue', 'sum')
        ).reset_index()
        state_perf['roas'] = state_perf['attributed_revenue'] / state_perf['spend']
        state_perf = state_perf.sort_values('spend', ascending=False).head(10)

        fig_state = px.bar(state_perf, x='state', y='spend', color='roas',
                           title="Top 10 States by Spend (Color = ROAS)",
                           hover_data=['roas', 'attributed_revenue'])
        st.plotly_chart(fig_state, use_container_width=True)
    else:
        st.warning("No data for selected state filters.")

with col_camp:
    st.subheader("Campaign Spend vs. ROAS")
    if not filtered_marketing.empty:
        campaigns = filtered_marketing.groupby(['campaign', 'tactic']).agg(
            spend=('spend', 'sum'),
            attributed_revenue=('attributed_revenue', 'sum'),
            impressions=('impressions', 'sum')
        ).reset_index()
        campaigns['roas'] = campaigns['attributed_revenue'] / (campaigns['spend'] + 1e-9)
        
        # --- EDITED LINE ---
        # The color parameter automatically distinguishes the bubbles by tactic
        fig_scatter = px.scatter(
            campaigns, 
            x='spend', 
            y='roas', 
            size='impressions',
            color='tactic',  # This is the key change
            hover_data=['campaign', 'tactic'], 
            title='Campaign Efficiency (Color = Tactic)',
            labels={'spend': 'Total Spend ($)', 'roas': 'Return on Ad Spend'}
        )
        # --- END OF EDIT ---
            
        st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.warning("No campaign data for current filters.")
        
# --- Data Table Expander ---
with st.expander("Show Detailed Daily Data"):
    st.dataframe(filtered_df.reset_index(drop=True).round(2))