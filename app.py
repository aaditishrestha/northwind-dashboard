import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sqlalchemy import create_engine, text

st.set_page_config(page_title="Northwind Sales Dashboard", layout="wide")
st.title("Northwind Sales Dashboard")

USER = "postgres.uzslpzounhragidwkmag"
PASSWORD = "northwindrain123"
HOST = "aws-0-ap-northeast-1.pooler.supabase.com"
PORT = "6543"
DBNAME = "postgres"
DB_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"

@st.cache_data
def load_data():
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        sales = pd.read_sql(text("""
        SELECT o.order_id,
               o.order_date,
               o.customer_id,
               c.company_name AS customer,
               c.country,
               e.first_name || ' ' || e.last_name AS employee,
               cat.category_name AS category,
               p.product_name AS product,
               od.quantity,
               od.unit_price * od.quantity * (1 - od.discount) AS revenue
            FROM order_details od
            JOIN orders o ON od.order_id = o.order_id
            JOIN customers c ON o.customer_id = c.customer_id
            JOIN employees e ON o.employee_id = e.employee_id
            JOIN products p ON od.product_id = p.product_id
            JOIN categories cat ON p.category_id = cat.category_id
        """), conn)

    sales['order_date'] = pd.to_datetime(sales['order_date'])
    return sales

sales = load_data()

def add_bar_labels(ax):
    for bar in ax.patches:
        ax.text(bar.get_width(), bar.get_y() + bar.get_height() / 2,
                f" ${bar.get_width():,.0f}", va='center', ha='left', fontsize=8)
        

st.sidebar.header("Filters")
country_options = ["All Countries"] + sorted(sales['country'].unique())
selected_country = st.sidebar.selectbox("Country", options=country_options)

category_options = sorted(sales['category'].unique())
selected_categories = st.sidebar.multiselect(
    "Category", options=category_options, default=category_options
)
min_date = sales['order_date'].min().date()
max_date = sales['order_date'].max().date()
date_range = st.sidebar.date_input("Date Range", value=(min_date, max_date),
                                   min_value=min_date, max_value=max_date)


if len(date_range) != 2:
    st.info("Please select an end date to continue.")
    st.stop()
if selected_country == "All Countries":
    country_mask = True
else:
    country_mask = sales['country'] == selected_country
filtered = sales[
    country_mask &
    sales['category'].isin(selected_categories) &
    (sales['order_date'].dt.date >= date_range[0]) &
    (sales['order_date'].dt.date <= date_range[1])
]
if filtered.empty:
    st.warning("No data for the selected filters.")
    st.stop()

total_revenue = filtered['revenue'].sum()
total_orders = filtered['order_id'].nunique()
total_customers = filtered['customer_id'].nunique()
avg_order_value = total_revenue / total_orders

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"${total_revenue:,.2f}")
col2.metric("Total Orders", f"{total_orders:,}")
col3.metric("Total Customers", f"{total_customers:,}")
col4.metric("Avg Order Value", f"${avg_order_value:,.2f}")

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("Monthly Revenue Trend")
    monthly = (
        filtered.assign(month=filtered['order_date'].dt.strftime('%Y-%m'))
        .groupby('month')['revenue'].sum()
        .reset_index()
    )
    fig1 = sns.relplot(x='month', y='revenue', data=monthly, kind='line',
                       marker='o', height=4, aspect=1.6)
    fig1.set_axis_labels('Month', 'Revenue ($)')
    fig1.ax.tick_params(axis='x', rotation=90)
    fig1.ax.grid(True, alpha=0.3)
    st.pyplot(fig1)


with right:
    st.subheader("Revenue by Category")
    category_rev = (
        filtered.groupby('category')['revenue'].sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    fig2 = sns.catplot(x='revenue', y='category', data=category_rev, kind='bar',
                       height=4, aspect=1.6)
    fig2.set_axis_labels('Revenue ($)', 'Category')
    add_bar_labels(fig2.ax)
    st.pyplot(fig2)

st.divider()

st.subheader("Order Line Data")
st.dataframe(filtered, hide_index=True)

st.download_button(
    "Download as CSV",
    filtered.to_csv(index=False),
    file_name="northwind_filtered.csv",
)

left, right = st.columns(2)
with left:
    st.subheader("Top 10 Products by Revenue")
    product_rev = (
        filtered.groupby('product')['revenue'].sum()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )
    fig3 = sns.catplot(x='revenue', y='product', data=product_rev, kind='bar',
                       height=4, aspect=1.6)
    fig3.set_axis_labels('Revenue ($)', 'Product')
    add_bar_labels(fig3.ax)
    st.pyplot(fig3)

with right:
    st.subheader("Revenue by Employee")
    employee_rev = (
        filtered.groupby('employee')['revenue'].sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    fig4 = sns.catplot(x='revenue', y='employee', data=employee_rev, kind='bar',
                       height=4, aspect=1.6)
    fig4.set_axis_labels('Revenue ($)', 'Employee')
    add_bar_labels(fig4.ax)
    st.pyplot(fig4)


st.dataframe(sales)







