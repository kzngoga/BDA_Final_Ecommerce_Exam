from pyspark.sql import SparkSession
from pymongo import MongoClient
import happybase

spark = SparkSession.builder.appName("CLVIntegration").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

# Pull user purchase data from MongoDB
mongo = MongoClient("mongodb://localhost:27017/")
db = mongo["ecommerce_analytics"]

print("\n=== Get user purchase data from MongoDB ===\n")
mongo_users = list(db.users.find({}, {
    "_id": 0,
    "user_id": 1,
    "purchase_summary.total_orders": 1,
    "purchase_summary.total_spent": 1
}))

users_df = spark.createDataFrame([
    {
        "user_id": u["user_id"],
        "total_orders": u["purchase_summary"]["total_orders"],
        "total_spent": u["purchase_summary"]["total_spent"]
    }
    for u in mongo_users
])
mongo.close()

# Pull session engagement data from HBase
hbase_conn = happybase.Connection('localhost', port=9090)
table = hbase_conn.table('user_sessions')

print("\n=== Get session engagement data from HBase ===\n")
session_stats = {}
for key, data in table.scan():
    user_id = key.decode().split("_")[0] + "_" + key.decode().split("_")[1]
    duration = int(data.get(b'session_info:duration_seconds', b'0'))
    if user_id not in session_stats:
        session_stats[user_id] = {"total_duration": 0, "session_count": 0}
    session_stats[user_id]["total_duration"] += duration
    session_stats[user_id]["session_count"] += 1

hbase_conn.close()

sessions_df = spark.createDataFrame([
    {
        "user_id": uid,
        "avg_session_duration": stats["total_duration"] / stats["session_count"],
        "session_count": stats["session_count"]
    }
    for uid, stats in session_stats.items()
])

# Join in Spark and compute CLV
combined = users_df.join(sessions_df, on="user_id", how="left").fillna(0)

combined.createOrReplaceTempView("user_engagement")

print("=== Customer Lifetime Value (CLV) Estimation ===")
spark.sql("""
    SELECT user_id,
           total_orders,
           total_spent,
           session_count,
           ROUND(avg_session_duration, 1) AS avg_session_duration_sec,
           ROUND(total_spent + (avg_session_duration / 60 * 0.5), 2) AS clv_score
    FROM user_engagement
    ORDER BY clv_score DESC
    LIMIT 10
""").show(truncate=False)

spark.stop()