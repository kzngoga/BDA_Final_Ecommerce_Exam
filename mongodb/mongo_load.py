import json
import os
from pymongo import MongoClient
from datetime import datetime


client = MongoClient("mongodb://localhost:27017/")
db = client["ecommerce_analytics"]

DATA_DIR = "./data"

def load_json(filename):
    with open(os.path.join(DATA_DIR, filename)) as f:
        return json.load(f)

# Build category lookup to enrich products with names
def build_category_lookup(categories):
    lookup = {}
    for cat in categories:
        for sub in cat.get("subcategories", []):
            lookup[(cat["category_id"], sub["subcategory_id"])] = {
                "category_name": cat["name"],
                "subcategory_name": sub["name"]
            }
        lookup[(cat["category_id"], None)] = {"category_name": cat["name"], "subcategory_name": None}
    return lookup

# Compute purchase summary per user from transactions
def build_purchase_summaries(transactions):
    summaries = {}
    for txn in transactions:
        uid = txn["user_id"]
        if uid not in summaries:
            summaries[uid] = {"total_orders": 0, "total_spent": 0.0, "last_purchase_date": None}
        summaries[uid]["total_orders"] += 1
        summaries[uid]["total_spent"] = round(summaries[uid]["total_spent"] + txn.get("total", 0), 2)
        date = txn.get("timestamp")
        if date and (summaries[uid]["last_purchase_date"] is None or date > summaries[uid]["last_purchase_date"]):
            summaries[uid]["last_purchase_date"] = date
    return summaries

print("Loading data...")
categories = load_json("categories.json")
products   = load_json("products.json")
users      = load_json("users.json")
transactions = load_json("transactions.json")

cat_lookup = build_category_lookup(categories)
purchase_summaries = build_purchase_summaries(transactions)

# Convert timestamp strings to datetime
for txn in transactions:
    txn["timestamp"] = datetime.fromisoformat(txn["timestamp"])

# Enrich products with category names
for p in products:
    info = cat_lookup.get((p["category_id"], p.get("subcategory_id"))) or \
           cat_lookup.get((p["category_id"], None), {})
    p["category_name"] = info.get("category_name")
    p["subcategory_name"] = info.get("subcategory_name")

# Enrich users with purchase summary
for u in users:
    u["purchase_summary"] = purchase_summaries.get(u["user_id"], {
        "total_orders": 0, "total_spent": 0.0, "last_purchase_date": None
    })

# Drop and reload collections
for col in ["products", "users", "transactions"]:
    db[col].drop()

db.products.insert_many(products)
db.products.create_index("product_id")
db.users.insert_many(users)
db.transactions.insert_many(transactions)

print(f"Products    : {db.products.count_documents({})}")
print(f"Users       : {db.users.count_documents({})}")
print(f"Transactions: {db.transactions.count_documents({})}")
client.close()