class DataAnalysis:
    def __init__(self, data_frame):
        self.data_frame = data_frame

    def get_daily_orders(self):
        daily_orders = self.data_frame.resample('D', on='order_approved_at').agg({
            "order_id": "nunique",
            "payment_value": "sum"
        }).reset_index()

        daily_orders.rename(columns={
            "order_id": "total_orders",
            "payment_value": "total_revenue"
        }, inplace=True)
        
        return daily_orders
    
    def get_total_spending(self):
        spending_df = self.data_frame.resample('D', on='order_approved_at').agg({
            "payment_value": "sum"
        }).reset_index()

        spending_df.rename(columns={
            "payment_value": "daily_spending"
        }, inplace=True)

        return spending_df

    def get_order_item_summary(self):
        item_summary = self.data_frame.groupby("product_category_name_english")["product_id"].count().reset_index()

        item_summary.rename(columns={
            "product_id": "items_sold"
        }, inplace=True)

        item_summary = item_summary.sort_values(by='items_sold', ascending=False)

        return item_summary

    def analyze_review_scores(self):
        review_counts = self.data_frame['review_score'].value_counts().sort_values(ascending=False)
        top_score = review_counts.idxmax()

        return review_counts, top_score

    def get_customer_distribution(self):
        customer_dist = self.data_frame.groupby("customer_state").customer_id.nunique().reset_index()

        customer_dist.rename(columns={
            "customer_id": "unique_customers"
        }, inplace=True)

        top_state = customer_dist.loc[customer_dist['unique_customers'].idxmax(), 'customer_state']
        customer_dist = customer_dist.sort_values(by='unique_customers', ascending=False)

        return customer_dist, top_state
    
    def calculate_rfm_metrics(self):
        rfm_metrics = self.data_frame.groupby("customer_id", as_index=False).agg({
            "order_approved_at": "max",  
            "order_id": "nunique",
            "payment_value": "sum"
        })

        rfm_metrics.columns = ["customer_id", "last_purchase_date", "purchase_frequency", "total_spent"]
        
        rfm_metrics["last_purchase_date"] = rfm_metrics["last_purchase_date"].dt.date
        latest_order_date = self.data_frame["order_approved_at"].dt.date.max()
        rfm_metrics["recency"] = rfm_metrics["last_purchase_date"].apply(lambda x: (latest_order_date - x).days)
        
        rfm_metrics.drop("last_purchase_date", axis=1, inplace=True)
    
        return rfm_metrics

class BrazilMapPlotter:
    def __init__(self, geo_data, matplotlib, image_module, url_module, streamlit):
        self.geo_data = geo_data
        self.matplotlib = matplotlib
        self.image_module = image_module
        self.url_module = url_module
        self.streamlit = streamlit

    def generate_map(self):
        brazil_map = self.image_module.imread(self.url_module.request.urlopen(
            'https://i.pinimg.com/originals/3a/0c/e1/3a0ce18b3c842748c255bc0aa445ad41.jpg'), 'jpg')

        ax = self.geo_data.plot(kind="scatter", x="geolocation_lng", y="geolocation_lat", 
                                figsize=(10,10), alpha=0.3, s=0.3, color='darkred')
        
        self.matplotlib.axis('off')
        self.matplotlib.imshow(brazil_map, extent=[-73.9828, -33.8, -33.7511, 5.4])

        self.streamlit.set_option('deprecation.showPyplotGlobalUse', False)
        self.streamlit.pyplot()
