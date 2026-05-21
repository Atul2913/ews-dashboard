import streamlit as st
import pandas as pd
import plotly.express as px
import base64

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(
    page_title="EWS Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# CUSTOM CSS
# ==========================================
st.markdown("""
<style>

html, body, [class*="css"] {
    font-family: 'Segoe UI', sans-serif;
}

/* MAIN BACKGROUND */
.main {
    background: #f4f7fb;
}

/* MAIN CONTAINER */
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    padding-left: 2rem;
    padding-right: 2rem;
}

/* SIDEBAR */
[data-testid="stSidebar"] {
    background: #0f172a;
    padding-top: 2rem;
}

[data-testid="stSidebar"] label {
    color: white !important;
    font-size: 15px !important;
    font-weight: 500 !important;
}

/* TITLE */
.dashboard-title {
    text-align: center;
    font-size: 52px;
    font-weight: 800;
    color: #111827;
    margin-bottom: 35px;
    letter-spacing: 1px;
}

/* KPI CARD */
.kpi-card {
    background: white;
    padding: 28px 20px;
    border-radius: 22px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    text-align: center;
    transition: 0.3s ease;
    border: 1px solid #e5e7eb;
    margin-bottom: 10px;
}

.kpi-card:hover {
    transform: translateY(-5px);
}

.kpi-title {
    font-size: 22px;
    font-weight: 600;
    margin-bottom: 15px;
    color: #374151;
}

.kpi-value {
    font-size: 42px;
    font-weight: 800;
    color: #111827;
}

/* SECTION BOX */
.section-box {
    background: white;
    padding: 25px;
    border-radius: 22px;
    margin-top: 25px;
    margin-bottom: 25px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    border: 1px solid #e5e7eb;
}

/* SECTION HEADINGS */
.section-heading {
    font-size: 26px;
    font-weight: 700;
    color: #111827;
    margin-bottom: 20px;
}

/* REPORT BOX */
.report-box {
    background: #f9fafb;
    padding: 25px;
    border-radius: 18px;
    line-height: 2;
    font-size: 16px;
    color: #1f2937;
    border: 1px solid #d1d5db;
}

/* METRIC COLORS */
.red {
    color: #ef4444;
}

.yellow {
    color: #f59e0b;
}

.green {
    color: #10b981;
}

.blue {
    color: #3b82f6;
}

/* TABLE */
[data-testid="stDataFrame"] {
    border-radius: 15px;
    overflow: hidden;
}

/* DOWNLOAD BUTTON */
.stDownloadButton button {
    width: 100%;
    background: #111827;
    color: white;
    border-radius: 12px;
    height: 50px;
    font-size: 16px;
    font-weight: 600;
    border: none;
}

.stDownloadButton button:hover {
    background: #2563eb;
    color: white;
}

/* FOOTER */
.footer {
    text-align: center;
    padding-top: 20px;
    color: gray;
    font-size: 14px;
}

</style>
""", unsafe_allow_html=True)

# ==========================================
# LOAD DATA
# ==========================================
df_full = pd.read_csv("output/final_ews_data.csv")

# ==========================================
# TITLE
# ==========================================
st.markdown(
    '<div class="dashboard-title">📊 EWS Dashboard</div>',
    unsafe_allow_html=True
)


# ==========================================
# SIDEBAR LOGO
# ==========================================
st.sidebar.markdown(
    """
    <style>
    .sidebar-logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        padding-top: 5px;
        padding-bottom: 20px;
    }

    .sidebar-logo-container img {
        width: 90%;
        max-width: 260px;
        height: auto;
        object-fit: contain;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# SIDEBAR LOGO
# ==========================================
st.sidebar.markdown(
    """
    <style>

    .logo-wrapper {
        width: 100%;
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: -10px;
        margin-bottom: 25px;
    }

    .logo-wrapper img {
        width: 230px;
        height: auto;
        object-fit: contain;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# FILTER TITLE
# ==========================================
st.sidebar.markdown(
    """
    <div style="
        color:white;
        font-size:30px;
        font-weight:800;
        margin-bottom:20px;
        margin-top:-5px;
    ">
    🔎 Filters
    </div>
    """,
    unsafe_allow_html=True
)

month = st.sidebar.selectbox(
    "Month",
    sorted(df_full['Month'].dropna().unique(), reverse=True)
)

df = df_full[df_full['Month'] == month].copy()

division = st.sidebar.multiselect(
    "Division",
    sorted(df['Division'].dropna().unique())
)

zone = st.sidebar.multiselect(
    "Zone",
    sorted(df['Zone Name'].dropna().unique())
)

manager_col = "Reporting to Territory Name"

if manager_col in df.columns:
    manager = st.sidebar.multiselect(
        "SD - Wise",
        sorted(df[manager_col].dropna().unique())
    )
else:
    manager = []

# ==========================================
# APPLY FILTERS
# ==========================================
if division:
    df = df[df['Division'].isin(division)]

if zone:
    df = df[df['Zone Name'].isin(zone)]

if manager:
    df = df[df[manager_col].isin(manager)]

# ==========================================
# KPI VALUES
# ==========================================
high = (df['Risk_Level'] == "High Risk").sum()
medium = (df['Risk_Level'] == "Medium Risk").sum()
low = (df['Risk_Level'] == "Low Risk").sum()

if 'Prev_Risk' in df.columns:
    new = (
        (df['Prev_Risk'] != "High Risk") &
        (df['Risk_Level'] == "High Risk")
    ).sum()
else:
    new = 0

# ==========================================
# KPI CARDS
# ==========================================
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title red">🔴 High Risk</div>
        <div class="kpi-value">{high}</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title yellow">🟡 Medium Risk</div>
        <div class="kpi-value">{medium}</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title green">🟢 Low Risk</div>
        <div class="kpi-value">{low}</div>
    </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title blue">🆕 New Risk</div>
        <div class="kpi-value">{new}</div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
# CHARTS SECTION
# ==========================================
st.markdown('<div class="section-box">', unsafe_allow_html=True)

col1, col2 = st.columns(2)

# Zone-wise
zone_df = (
    df[df['Risk_Level'] == "High Risk"]
    .groupby('Zone Name')
    .size()
    .reset_index(name='Count')
)

fig1 = px.bar(
    zone_df,
    x='Zone Name',
    y='Count',
    text='Count',
    color='Count',
    template='plotly_white'
)

fig1.update_layout(
    title="📍 Zone-wise High Risk",
    title_font_size=22,
    xaxis_title="Zone",
    yaxis_title="Employees",
    height=450
)

fig1.update_traces(textposition='outside')

col1.plotly_chart(fig1, use_container_width=True)

# Pie chart
fig2 = px.pie(
    df,
    names='Risk_Level',
    hole=0.5,
    template='plotly_white'
)

fig2.update_layout(
    title="🍩 Risk Distribution",
    title_font_size=22,
    height=450
)

col2.plotly_chart(fig2, use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# TREND + MANAGER
# ==========================================
st.markdown('<div class="section-box">', unsafe_allow_html=True)

col1, col2 = st.columns(2)

trend_df = (
    df_full[df_full['Risk_Level'] == "High Risk"]
    .groupby('Month')
    .size()
    .reset_index(name='Count')
)

fig3 = px.line(
    trend_df,
    x='Month',
    y='Count',
    text='Count',
    markers=True,
    template='plotly_white'
)

fig3.update_layout(
    title="📈 High Risk Trend",
    title_font_size=22,
    height=450
)

col1.plotly_chart(fig3, use_container_width=True)

if manager_col in df.columns:

    mgr_df = (
        df[df['Risk_Level'] == "High Risk"]
        .groupby(manager_col)
        .size()
        .reset_index(name='Count')
    )

    fig4 = px.bar(
        mgr_df,
        x=manager_col,
        y='Count',
        text='Count',
        color='Count',
        template='plotly_white'
    )

    fig4.update_layout(
        title="👨‍💼 SD - Wise Risk",
        title_font_size=22,
        xaxis_tickangle=-35,
        height=450
    )

    col2.plotly_chart(fig4, use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# HIGH RISK TABLE
# ==========================================
st.markdown('<div class="section-box">', unsafe_allow_html=True)

st.markdown(
    '<div class="section-heading">🔥 Top High Risk Employees</div>',
    unsafe_allow_html=True
)

top_df = (
    df[df['Risk_Level'] == "High Risk"]
    .sort_values(by='EWS_Score', ascending=False)
    .head(10)
    .reset_index(drop=True)
)

# ==========================================
# SERIAL NUMBER
# ==========================================

top_df.insert(
    0,
    "Sr No",
    range(1, len(top_df) + 1)
)

# ==========================================
# DISPLAY TABLE
# ==========================================

display_cols = [
    'Sr No',
    'Employee Name',
    'Designation',
    'Zone Name',
    'EWS_Score'
]

available_cols = [
    c for c in display_cols
    if c in top_df.columns
]

st.dataframe(
    top_df[available_cols],
    use_container_width=True,
    height=400,
    hide_index=True
)

st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# NEW HIGH RISK EMPLOYEES
# ==========================================
st.markdown('<div class="section-box">', unsafe_allow_html=True)

st.markdown(
    '<div class="section-heading">🚨 New High Risk Employees</div>',
    unsafe_allow_html=True
)

if 'Prev_Risk' in df.columns:

    new_risk_df = df[
        (
            (df['Prev_Risk'] != "High Risk") |
            (df['Prev_Risk'].isna())
        ) &
        (df['Risk_Level'] == "High Risk")
    ]

else:

    new_risk_df = df[df['Risk_Level'] == "High Risk"]

# ==========================================
# SERIAL NUMBER
# ==========================================

new_risk_df = (
    new_risk_df
    .reset_index(drop=True)
)

new_risk_df.insert(
    0,
    "Sr No",
    range(1, len(new_risk_df) + 1)
)

show_cols = [
    'Sr No',
    'Employee Name',
    'Designation',
    'Zone Name',
    'Division',
    'Coverage',
    'Discount Percentage',
    'Closing Stock Days',
    'EWS_Score'
]

available_cols = [
    c for c in show_cols
    if c in new_risk_df.columns
]

st.dataframe(
    new_risk_df[available_cols],
    use_container_width=True,
    height=450,
    hide_index=True
)

st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# EXECUTIVE REPORT
# ==========================================
st.markdown(f"""
<div class="report-box">

<h3 style="color:#2563eb;">
🤖 Executive AI Insights
</h3>

<p>{report_text.replace(chr(10), "<br><br>")}</p>

</div>
""", unsafe_allow_html=True)

# ==========================================
# EXTRACT REQUIRED SECTIONS
# ==========================================
sections = {}
current_section = None

for line in report_text.splitlines():

    line = line.strip()

    if line.startswith("---") and line.endswith("---"):

        current_section = line.replace("-", "").strip()

        sections[current_section] = []

    elif current_section and line:

        sections[current_section].append(line)

trend_section = "<br>".join(
    sections.get("TREND", [])
)

actions_section = "<br>".join(
    sections.get("ACTIONS", [])
)

ai_section = "<br>".join(
    sections.get("AI INSIGHTS", [])
)

# ==========================================
# DISPLAY SHORT REPORT
# ==========================================
st.markdown(f"""
<div class="report-box">

<h3 style="color:#2563eb;">📈 Trend</h3>
<p>{trend_section}</p>

<br>

<h3 style="color:#dc2626;">🎯 Actions</h3>
<p>{actions_section}</p>

<br>

<h3 style="color:#16a34a;">🤖 AI Insights</h3>
<p>{ai_section}</p>

</div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# DOWNLOAD BUTTON
# ==========================================
csv = df.to_csv(index=False)

st.download_button(
    "📥 Download Report",
    csv,
    "EWS_Data.csv"
)

# ==========================================
# FOOTER
# ==========================================
st.markdown(
    '<div class="footer">Developed by Atul Tembhare</div>',
    unsafe_allow_html=True
)
