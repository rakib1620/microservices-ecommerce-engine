import os
import json
import time
import redis

# Environment variables theke connection parameters newa
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Redis connection establish kora
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

print("Worker started. Listening for orders in queue...", flush=True)

while True:
    try:
        # 1. Safely fetch from blpop
        result = redis_client.blpop("order_queue", timeout=5)
        
        # 2. Check if result is None (timeout case)
        if result is None:
            continue
            
        queue_name, order_data_json = result
        
        if order_data_json:
            order = json.loads(order_data_json)
            print(f"Processing Order ID: {order['order_id']} for Item: {order['item_name']}...", flush=True)

            # Simulated heavy task (e.g., Database write or Payment processing delay)
            time.sleep(2)

            print(f"Successfully processed Order ID: {order['order_id']}", flush=True)
            
    except Exception as e:
        print(f"Error processing order: {e}", flush=True)
        time.sleep(2)
