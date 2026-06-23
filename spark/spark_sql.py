from pyspark.sql import SparkSession
from pyspark.sql.functions import explode, col

spark = SparkSession.builder.appName("EcommerceSparkSQL").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

# Load data
print("\n=== Loading data ===\n")
transactions = spark.read.json("./data/transactions.json")
products = spark.read.json("./data/products.json")
categories = spark.read.json("./data/categories.json")
 
# Add category_name to products via category_id
products = products.join(
    categories.select("category_id", col("name").alias("category_name")),
    on="category_id",
    how="left"
)

# Flatten items array so each line item is its own row
items = transactions.select(
    "transaction_id", "user_id", "payment_method", "status",
    explode("items").alias("item")
).select(
    "transaction_id", "user_id", "payment_method", "status",
    col("item.product_id").alias("product_id"),
    col("item.subtotal").alias("subtotal")
)

# Register dataframes as SQL tables
items.createOrReplaceTempView("transaction_items")
products.createOrReplaceTempView("products")

# Query 1: Revenue by category
print("=== Revenue by Category ===")
spark.sql("""
    SELECT p.category_name, ROUND(SUM(t.subtotal), 2) AS total_revenue
    FROM transaction_items t
    JOIN products p ON t.product_id = p.product_id
    WHERE t.status = 'completed'
    GROUP BY p.category_name
    ORDER BY total_revenue DESC
    LIMIT 10
""").show(truncate=False)

# Query 2: Average order value by payment method
print("=== Average Order Value by Payment Method ===")
spark.sql("""
    SELECT payment_method,
           ROUND(AVG(subtotal), 2) AS avg_item_value,
           COUNT(*) AS num_items
    FROM transaction_items
    WHERE status = 'completed'
    GROUP BY payment_method
    ORDER BY avg_item_value DESC
""").show(truncate=False)

spark.stop()