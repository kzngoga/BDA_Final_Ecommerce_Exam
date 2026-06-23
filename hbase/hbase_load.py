import json
import happybase

connection = happybase.Connection('localhost', port=9090)
table = connection.table('user_sessions')

SAMPLE_SIZE = 5000

with open("./data/sessions_0.json") as f:
    sessions = json.load(f)[:SAMPLE_SIZE]

# Row key: user_id + start_time, for sorting sessions by user then time stamp
with table.batch(batch_size=500) as b:
    for s in sessions:
        row_key = f"{s['user_id']}_{s['start_time']}"
        b.put(row_key, {
            b'session_info:start_time': s['start_time'],
            b'session_info:end_time': s['end_time'],
            b'session_info:duration_seconds': str(s['duration_seconds']),
            b'session_info:device_type': s['device_profile']['type'],
            b'session_info:browser': s['device_profile']['browser'],
            b'session_info:referrer': s['referrer'],
            b'session_info:conversion_status': s['conversion_status'],
            b'activity:viewed_products': ",".join(s['viewed_products']),
            b'activity:page_view_count': str(len(s['page_views'])),
        })

print(f"Loaded {len(sessions)} sessions into HBase")
connection.close()