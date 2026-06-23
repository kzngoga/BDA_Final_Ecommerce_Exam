import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["ecommerce_analytics"]

# Data: Top 10 Products by Revenue
top_products = list(db.transactions.aggregate([
    {"$match": {"status": "completed"}},
    {"$unwind": "$items"},
    {"$group": {"_id": "$items.product_id", "total_revenue": {"$sum": "$items.subtotal"}}},
    {"$lookup": {"from": "products", "localField": "_id", "foreignField": "product_id", "as": "product"}},
    {"$unwind": "$product"},
    {"$project": {"_id": 0, "name": "$product.name", "total_revenue": 1}},
    {"$sort": {"total_revenue": -1}},
    {"$limit": 10}
]))

# Data: Revenue by Category
categories = list(db.transactions.aggregate([
    {"$match": {"status": "completed"}},
    {"$unwind": "$items"},
    {"$lookup": {"from": "products", "localField": "items.product_id", "foreignField": "product_id", "as": "product"}},
    {"$unwind": "$product"},
    {"$group": {"_id": "$product.category_name", "total_revenue": {"$sum": "$items.subtotal"}}},
    {"$sort": {"total_revenue": -1}},
    {"$limit": 10}
]))

# Data: Monthly Revenue Trend
monthly = list(db.transactions.aggregate([
    {"$match": {"status": "completed"}},
    {"$unwind": "$items"},
    {"$group": {
        "_id": {"year": {"$year": "$timestamp"}, "month": {"$month": "$timestamp"}},
        "monthly_revenue": {"$sum": "$items.subtotal"}
    }},
    {"$sort": {"_id.year": 1, "_id.month": 1}}
]))
for m in monthly:
    m["month_label"] = f"{m['_id']['year']}-{m['_id']['month']:02d}"

# Data: Customer Spending Distribution
spending = [
    u["purchase_summary"]["total_spent"]
    for u in db.users.find({}, {"purchase_summary.total_spent": 1})
    if u["purchase_summary"]["total_spent"] > 0
]

client.close()

# Build 2x2 dashboard
fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        "Top 10 Products by Revenue",
        "Revenue by Category",
        "Monthly Revenue Trend",
        "Customer Segmentation by Spending"
    )
)

# Chart 1: horizontal bar
fig.add_trace(go.Bar(
    x=[p["total_revenue"] for p in top_products][::-1],
    y=[p["name"] for p in top_products][::-1],
    orientation="h", marker_color="steelblue", showlegend=False
), row=1, col=1)

# Chart 2: vertical bar
fig.add_trace(go.Bar(
    x=[c["_id"] for c in categories],
    y=[c["total_revenue"] for c in categories],
    marker_color="darkorange", showlegend=False
), row=1, col=2)

# Chart 3: line
fig.add_trace(go.Scatter(
    x=[m["month_label"] for m in monthly],
    y=[m["monthly_revenue"] for m in monthly],
    mode="lines+markers", line_color="seagreen", showlegend=False
), row=2, col=1)

# Chart 4: histogram
fig.add_trace(go.Histogram(
    x=spending, nbinsx=30, marker_color="mediumpurple", showlegend=False
), row=2, col=2)

fig.update_layout(
    height=800, width=1200,
    title_text="E-commerce Analytics Dashboard"
)

fig.update_yaxes(automargin=True, row=1, col=1)

fig.write_html("./output/dashboard.html")
print("Dashboard saved to ./output/dashboard.html")