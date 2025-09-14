#  Marketing Intelligence Dashboard

An interactive **Business Intelligence (BI) dashboard** built with **Streamlit** to analyze marketing and business data for an e-commerce brand.  
The dashboard connects campaign-level marketing activities from **Facebook**, **Google**, and **TikTok** with business outcomes like **revenue**, **profit**, and **customer acquisition**.

Its primary goal is to give stakeholders a **clear, actionable tool** to understand marketing effectiveness, identify high-performing strategies, and make **data-driven decisions** to optimize advertising spend.

---

##  Overview

This dashboard allows you to:
- Track **ad spend**, **revenue**, and **ROAS** over time.
- Analyze **channel, tactic, and state-level performance**.
- Visualize **key business metrics** alongside marketing data.
- Identify **opportunities and underperforming campaigns** quickly.

---

##  Key Features

 **Executive KPI Summary**: 
High-level overview of Total Revenue, Ad Spend, Marketing Efficiency Ratio (MER), and Customer Acquisition Cost (CAC).

 **Interactive Filters**: 
Slice data by **date range**, **marketing platform**, **state**, and **advertising tactic**.

 **Dynamic Insights & Recommendations**: 
An automated insights engine highlights **top performers**, **hidden opportunities**, and **campaigns to review**.

 **Performance Trend Analysis**: 
Time-series charts visualize trends in **revenue** and **gross profit**.

 **Channel & Tactic Breakdown**:  
Side-by-side comparisons of **ROAS** for each marketing platform and tactic.

 **Granular Deep Dives**:  
State-level and campaign-level performance, including an **efficiency scatter plot** (Spend vs ROAS) to identify outliers.

---

##  Data Sources

This project uses **four datasets** capturing 120 days of daily activity:

| Dataset        | Description |
|---------------|-------------|
| **Facebook.csv** | Campaign-level marketing data (date, tactic, state, campaign, impressions, clicks, spend, attributed_revenue). |
| **Google.csv** | Same format as above for Google Ads. |
| **TikTok.csv** | Same format as above for TikTok Ads. |
| **Business.csv** | Daily business performance (orders, new orders, new customers, total revenue, gross profit, COGS). |

---

##  Tech Stack

- **Language**: Python  
- **Libraries**:
  - [Streamlit](https://streamlit.io/) → Build and serve the interactive dashboard
  - [Pandas](https://pandas.pydata.org/) → Data manipulation & cleaning
  - [NumPy](https://numpy.org/) → Efficient numerical calculations
  - [Plotly Express](https://plotly.com/python/plotly-express/) → Interactive visualizations

---

##  Setup & Installation

Follow these steps to run the dashboard locally:

### 1️. Clone the Repository
```bash
git clone https://github.com/your-username/your-repository-name.git
cd your-repository-name
```
### 2. Install Dependencies

Make sure you have a requirements.txt file with:

streamlit
pandas
numpy
plotly

Then install:
```bash
pip install -r requirements.txt
```
### 3. Organize Data

Create a data folder in the root directory and place the four CSV files inside:

Facebook.csv

Google.csv

TikTok.csv

business.csv

### 4. Run the App
```bash
streamlit run app.py
```
The dashboard will open automatically in your browser.

---
### Insights & Decision-Making

This dashboard helps stakeholders:

Monitor marketing ROI in near real-time.

Detect state-level trends and focus spending effectively.

Compare channels and tactics to allocate budgets more efficiently.

Track customer growth alongside marketing activity.

### Deployed Link
```bash
https://ad-performance-dashboard.streamlit.app/
```