import os
import json
import time
import redis

# Redis connection setup from environment variables
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

print("Starting Background Worker and connecting to Redis...")
try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    print("Successfully connected to Redis!")
except Exception as e:
    print(f"Redis connection error in worker: {e}")

def process_orders():
    """
    Continuously listen to the Redis queue ('order_queue') 
    and process background order tasks.
    """
    print("Worker is listening for orders in the queue...")
    while True:
        try:
            # Блокирующий pop (BRPOP) অথবা সাধারণ RPOP ব্যবহার করে কিউ থেকে ডেটা আনা
            # এখানে আমরা রিমোট কিউ থেকে ডেটা তুলছি
            queue_data = redis_client.rpop("order_queue")
            
            if queue_data:
                order_data = json.loads(queue_data)
                order_id = order_data.get("order_id")
                item_name = order_data.get("item_name")
                
                print(f"\n[PROCESSING] Found new order ID: {order_id} for item: {item_name}")
                
                # সিমুলেশন: অর্ডার প্রসেস হতে কিছুটা সময় লাগছে (যেমন: পেমেন্ট গেটওয়ে চেক, ইনভেন্টরি আপডেট ইত্যাদি)
                time.sleep(3)
                
                print(f"[SUCCESS] Order ID {order_id} has been successfully processed and completed!\n")
            else:
                # কিউ খালি থাকলে ১ সেকেন্ড পর আবার চেক করবে
                time.sleep(1)
                
        except Exception as e:
            print(f"Error processing order: {e}")
            time.sleep(2)

if __name__ == "__main__":
    process_orders()
