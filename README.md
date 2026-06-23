# E-commerce Multi-Model Analytics

AUCA Big Data Analytics final project — analytics system using MongoDB, HBase, and Apache Spark on a synthetic e-commerce dataset.

## Setup

### 1. Install dependencies
```bash
pip install faker pandas pymongo happybase plotly
```

### 2. Generate the dataset
```bash
python dataset_generator.py
```
Produces the files in the project root. Move them into a `data/` folder.

### 3. Start required services
- **MongoDB** — running locally on port 27017
- **HBase** — Docker container with ports `16000, 16010, 16020, 16030, 2181, 9090` exposed
  ```bash
  docker run -d --name hbase \
    -p 16000:16000 -p 16010:16010 -p 16020:16020 -p 16030:16030 \
    -p 2181:2181 -p 9090:9090 \
    harisekhon/hbase:latest
  ```
- **Spark** — installed locally, accessible via `spark-submit`

### 4. Create the HBase table
```bash
docker exec -it hbase hbase shell
create 'user_sessions', 'session_info', 'activity'
```

## Running the pipeline

| Step | Command |
|---|---|
| Load data into MongoDB | `python mongodb/mongo_load.py` |
| Run MongoDB aggregations | `python mongodb/mongo_queries.py` |
| Load sessions into HBase | `python hbase/hbase_load.py` |
| Query HBase sessions for a user | `scan 'user_sessions', {'ROWPREFIXFILTER' => 'user_000000'}` (in HBase shell) |
| Spark batch processing (product recommendations) | `spark-submit --driver-memory 4g spark/spark_batch.py` |
| Spark SQL analytics (revenue by category) | `spark-submit --driver-memory 4g spark/spark_sql.py` |
| CLV integration (MongoDB + HBase + Spark) | `spark-submit --driver-memory 4g spark/clv_integration.py` |
| Generate visualizations dashboard | `python visualizations/visualizations.py` |

Output dashboard: `output/dashboard.html`