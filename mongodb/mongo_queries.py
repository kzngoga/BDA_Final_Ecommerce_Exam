from pymongo import MongoClient
from collections import defaultdict

client = MongoClient("mongodb://localhost:27017/")
db = client["ecommerce_analytics"]

# Pipeline 1: Top 10 Products by Revenue
print("=" * 60)
print("PIPELINE 1: Top 10 Products by Total Revenue")
print("=" * 60)

pipeline_1 = [
    {"$match": {"status": "completed"}},
    {"$unwind": "$items"},
    {"$group": {
        "_id": "$items.product_id",
        "total_revenue": {"$sum": "$items.subtotal"},
        "total_units_sold": {"$sum": "$items.quantity"},
        "num_transactions": {"$sum": 1}
    }},
    {"$lookup": {
        "from": "products",
        "localField": "_id",
        "foreignField": "product_id",
        "as": "product"
    }},
    {"$unwind": "$product"},
    {"$project": {
        "_id": 0,
        "product_id": "$_id",
        "name": "$product.name",
        "category": "$product.category_name",
        "total_revenue": {"$round": ["$total_revenue", 2]},
        "total_units_sold": 1,
        "num_transactions": 1
    }},
    {"$sort": {"total_revenue": -1}},
    {"$limit": 10}
]

for i, r in enumerate(db.transactions.aggregate(pipeline_1), 1):
    print(f"{r['name']} | ${r['total_revenue']:.2f} | Units: {r['total_units_sold']}")

# Pipeline 2: Monthly Revenue by Category
print("\n" + "=" * 60)
print("PIPELINE 2: Monthly Revenue by Category")
print("=" * 60)

pipeline_2 = [
    {"$match": {"status": "completed"}},
    {"$unwind": "$items"},
    {"$lookup": {
        "from": "products",
        "localField": "items.product_id",
        "foreignField": "product_id",
        "as": "product"
    }},
    {"$unwind": "$product"},
    {"$group": {
        "_id": {
            "year":  {"$year": "$timestamp"},
            "month": {"$month": "$timestamp"},
            "category": "$product.category_name"
        },
        "monthly_revenue": {"$sum": "$items.subtotal"},
        "num_orders": {"$sum": 1}
    }},
    {"$project": {
        "_id": 0,
        "year": "$_id.year",
        "month": "$_id.month",
        "category": "$_id.category",
        "monthly_revenue": {"$round": ["$monthly_revenue", 2]},
        "num_orders": 1
    }},
    {"$sort": {"year": 1, "month": 1, "monthly_revenue": -1}}
]

monthly = defaultdict(list)
for r in db.transactions.aggregate(pipeline_2):
    monthly[f"{r['year']}-{r['month']:02d}"].append(r)

for month, entries in sorted(monthly.items()):
    print(f"\n{month}:")
    for e in entries[:3]:
        print(f"{e['year']}-{e['month']:02d} | {e['category']} | ${e['monthly_revenue']:.2f} | Orders: {e['num_orders']}")

client.close()