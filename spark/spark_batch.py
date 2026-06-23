from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode, count

spark = SparkSession.builder \
    .appName("EcommerceAnalytics") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

# Load the datasets
print("Loading data...")
transactions = spark.read.json("./data/transactions.json")
users = spark.read.json("./data/users.json")
products = spark.read.json("./data/products.json")

# Data Cleaning
print("\n=== Data Cleaning ===")

# Drop rows with missing critical fields
transactions = transactions.dropna(subset=["transaction_id", "user_id", "timestamp"])
users = users.dropna(subset=["user_id", "registration_date"])
products = products.dropna(subset=["product_id", "base_price"])

# Filter completed transactions
transactions = transactions.filter(col("status") == "completed")

print(f"Transactions (completed): {transactions.count()}")
print(f"Users: {users.count()}")
print(f"Products: {products.count()}")

# Product Recommendations ("users who bought X also bought Y")
print("\n=== Product Recommendations ===")

# Flatten transaction items
items = transactions.select("transaction_id", "user_id", explode("items").alias("item")) \
    .select("transaction_id", "user_id", col("item.product_id").alias("product_id"))

# Self-join to find products bought together in the same transaction
pairs = items.alias("a").join(
    items.alias("b"),
    (col("a.transaction_id") == col("b.transaction_id")) &
    (col("a.product_id") < col("b.product_id"))  # avoid duplicates and self-pairs
).select(
    col("a.product_id").alias("product_a"),
    col("b.product_id").alias("product_b")
)

# Count bought together times
recommendations = pairs.groupBy("product_a", "product_b") \
    .agg(count("*").alias("times_bought_together")) \
    .orderBy(col("times_bought_together").desc())

print("Top 10 product pairs bought together:")
recommendations.show(10, truncate=False)

spark.stop()