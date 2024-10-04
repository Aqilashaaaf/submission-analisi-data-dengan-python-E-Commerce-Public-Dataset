import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import urllib
import math
from babel.numbers import format_currency

# Set style for seaborn
sns.set(style='darkgrid')

# Load datasets
date_cols = [
    "order_approved_at", "order_delivered_carrier_date", 
    "order_delivered_customer_date", "order_estimated_delivery_date", 
    "order_purchase_timestamp", "shipping_limit_date"
]

# Read main dataset
data_url = "https://raw.githubusercontent.com/AqilaShafaFazira/submission-analisi-data-dengan-python-E-Commerce-Public-Dataset/main/Dashboard/all_data.csv"
main_data = pd.read_csv(data_url)

# Sort and reset index
main_data.sort_values(by="order_approved_at", inplace=True)
main_data.reset_index(drop=True, inplace=True)

# Load geolocation data
geo_data_url = "https://raw.githubusercontent.com/AqilaShafaFazira/submission-analisi-data-dengan-python-E-Commerce-Public-Dataset/main/Data/geolocation_dataset.csv"
geo_data = pd.read_csv(geo_data_url)

# Convert date columns to datetime
for col in date_cols:
    main_data[col] = pd.to_datetime(main_data[col])

# Get min and max dates for date input
min_date = main_data["order_approved_at"].min().date()
max_date = main_data["order_approved_at"].max().date()

# Streamlit sidebar for user input
with st.sidebar:
    # Display logo
    st.image("https://raw.githubusercontent.com/AqilaShafaFazira/submission-analisi-data-dengan-python-E-Commerce-Public-Dataset/main/Data/logo.jpeg", width=100)

    # Date selection
    date_range = st.date_input(
        label="Select Date Range",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )

# Filter main data based on selected dates
filtered_data = main_data[
    (main_data["order_approved_at"].dt.date >= date_range[0]) & 
    (main_data["order_approved_at"].dt.date <= date_range[1])
]

# Initialize data analyzer
class DataAnalyzer:
    def __init__(self, data):
        self.data = data

    def create_daily_orders_df(self):
        daily_orders = self.data.resample('D', on='order_approved_at').agg({
            'order_id': 'count',
            'payment_value': 'sum'
        }).reset_index()
        daily_orders.columns = ['order_approved_at', 'order_count', 'revenue']
        return daily_orders

    def create_sum_spend_df(self):
        return self.data.groupby('order_approved_at').agg({
            'payment_value': 'sum'
        }).reset_index().rename(columns={'payment_value': 'total_spend'})

    def create_sum_order_items_df(self):
        return self.data.groupby('product_category_name_english').agg({
            'order_item_id': 'count'
        }).reset_index().rename(columns={'order_item_id': 'product_count'}).sort_values('product_count', ascending=False)

    def review_score_df(self):
        review_scores = self.data['review_score'].value_counts().sort_index()
        frequent_scores = review_scores.idxmax()
        return review_scores, frequent_scores

    def create_rfm_df(self):
        rfm = self.data.groupby('customer_unique_id').agg({
            'order_approved_at': lambda x: (self.data['order_approved_at'].max() - x.max()).days,
            'order_id': 'count',
            'payment_value': 'sum'
        })
        rfm.columns = ['recency', 'frequency', 'monetary']
        return rfm

    def create_bystate_df(self):
        state_summary = self.data.groupby('customer_state').agg({
            'order_id': 'count',
            'payment_value': 'sum'
        }).reset_index()
        state_summary.columns = ['state', 'total_orders', 'total_revenue']
        most_common_state = state_summary.loc[state_summary['total_orders'].idxmax(), 'state']
        return state_summary, most_common_state

data_analyzer = DataAnalyzer(filtered_data)

# Generate various dataframes for analysis
daily_order_df = data_analyzer.create_daily_orders_df()
total_spending_df = data_analyzer.create_sum_spend_df()
item_summary_df = data_analyzer.create_sum_order_items_df()
review_scores, frequent_scores = data_analyzer.review_score_df()
rfm_df = data_analyzer.create_rfm_df()
state_summary_df, most_common_state = data_analyzer.create_bystate_df()

# App title
st.title("E-Commerce Public Dataset")

# Dashboard introduction
st.write("**This dashboard is used to analyze E-Commerce public data.**")

# Display total orders and revenue
st.subheader("Total Orders")
col1, col2 = st.columns(2)

with col1:
    total_orders = daily_order_df["order_count"].sum()
    formatted_orders = "{:,.0f}".format(total_orders)
    st.markdown(f"Total Orders: **{formatted_orders}**")

with col2:
    total_revenue = daily_order_df["revenue"].sum()
    formatted_revenue = "${:,.2f}".format(total_revenue)
    st.markdown(f"Total Revenue: **{formatted_revenue}**")

# Plot daily orders graph
fig, ax = plt.subplots(figsize=(12, 6))
sns.lineplot(
    x=daily_order_df["order_approved_at"],
    y=daily_order_df["order_count"],
    marker="o",
    linewidth=2,
    color="#90CAF9"
)
ax.tick_params(axis="x", rotation=45)
ax.tick_params(axis="y", labelsize=15)
ax.set_xlabel("Order Date", fontsize=15)
ax.set_ylabel("Total Orders", fontsize=15)
st.pyplot(fig)

# Customer spending analysis
st.subheader("Amount Spent by Consumers")
col1, col2 = st.columns(2)

with col1:
    total_spent = total_spending_df["total_spend"].sum()
    formatted_spending = "${:,.2f}".format(total_spent)
    st.markdown(f"Total Spending: **{formatted_spending}**")

with col2:
    avg_spending = total_spending_df["total_spend"].mean()
    formatted_avg_spending = "${:,.2f}".format(avg_spending)
    st.markdown(f"Average Spending: **{formatted_avg_spending}**")

# Plot total spending over time
fig, ax = plt.subplots(figsize=(12, 6))
sns.lineplot(
    data=total_spending_df,
    x="order_approved_at",
    y="total_spend",
    marker="o",
    linewidth=2,
    color="#90CAF9"
)

ax.tick_params(axis="x", rotation=45)
ax.tick_params(axis="y", labelsize=15)
ax.set_xlabel("Order Date", fontsize=15)
ax.set_ylabel("Total Spending", fontsize=15)
st.pyplot(fig)

# Ordered items analysis
st.subheader("Ordered Items")
col1, col2 = st.columns(2)

with col1:
    total_items_ordered = item_summary_df["product_count"].sum()
    st.markdown(f"Total Items Ordered: **{total_items_ordered:,}**")

with col2:
    avg_items_ordered = math.ceil(item_summary_df["product_count"].mean())
    st.markdown(f"Average Items Ordered: **{avg_items_ordered}**")

# Plot ordered items graph
fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(20, 10))

sns.barplot(x="product_count", y="product_category_name_english", data=item_summary_df.head(5), palette="viridis", ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel("Number of Sales", fontsize=12)
ax[0].set_title("Top Selling Products", loc="center", fontsize=14)
ax[0].tick_params(axis='y', labelsize=10)
ax[0].tick_params(axis='x', labelsize=10)

sns.barplot(x="product_count", y="product_category_name_english", data=item_summary_df.sort_values(by="product_count", ascending=True).head(5), palette="viridis", ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel("Number of Sales", fontsize=12)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Least Selling Products", loc="center", fontsize=14)
ax[1].tick_params(axis='y', labelsize=10)
ax[1].tick_params(axis='x', labelsize=10)

st.pyplot(fig)

# Review score analysis
st.subheader("Review Scores")
col1, col2 = st.columns(2)

with col1:
    average_review = round(review_scores.mean(), 2)
    st.markdown(f"Average Review Score: **{average_review}**")

with col2:
    most_common_review = review_scores.index[review_scores.argmax()]
    st.markdown(f"Most Common Review Score: **{most_common_review}**")

fig, ax = plt.subplots(figsize=(12, 6))
colors = sns.color_palette("viridis", len(review_scores))

sns.barplot(x=review_scores.index,
            y=review_scores.values,
            order=review_scores.index,
            palette=colors)

plt.title("Customer Review Scores for Service", fontsize=15)
plt.xlabel("Score")
plt.ylabel("Count")
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)

# Add labels above bars
for i, value in enumerate(review_scores.values):
    ax.text(i, value + 5, str(value), ha='center', va='bottom', fontsize=12, color='black')

st.pyplot(fig)

# RFM Analysis
st.subheader("Best Customers Based on RFM Analysis")

col1, col2, col3 = st.columns(3)

with col1:
    avg_recency = round(rfm_df.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)

with col2:
    avg_frequency = round(rfm_df.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)

with col3:
    avg_monetary = format_currency(rfm_df.monetary.mean(), "USD", locale='en_US') 
    st.metric("Average Monetary", value=avg_monetary)

fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(20, 6))

sns.scatterplot(x='recency', y='frequency', data=rfm_df, ax=ax[0])
ax[0].set_title("Recency vs Frequency", fontsize=14)
ax[0].set_xlabel("Recency", fontsize=12)
ax[0].set_ylabel("Frequency", fontsize=12)

sns.scatterplot(x='frequency', y='monetary', data=rfm_df, ax=ax[1])
ax[1].set_title("Frequency vs Monetary", fontsize=14)
ax[1].set_xlabel("Frequency", fontsize=12)
ax[1].set_ylabel("Monetary", fontsize=12)

sns.scatterplot(x='recency', y='monetary', data=rfm_df, ax=ax[2])
ax[2].set_title("Recency vs Monetary", fontsize=14)
ax[2].set_xlabel("Recency", fontsize=12)
ax[2].set_ylabel("Monetary", fontsize=12)

st.pyplot(fig)

# Display analysis results data
st.subheader("Analysis Results Data")
st.dataframe(filtered_data)

# Add footer
st.write("**Aqila Shafa Fazira**")