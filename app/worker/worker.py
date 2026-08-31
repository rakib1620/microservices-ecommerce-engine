import os
import json
import time
import redis


def get_redis_client():
    """Build a Redis connection using environment variables, with sane defaults."""
    host = os.getenv("REDIS_HOST", "redis")
    port = int(os.getenv("REDIS_PORT", 6379))
    return redis.Redis(host=host, port=port, decode_responses=True)


def process_order(order: dict) -> None:
    """
    Process a single order (simulates payment/DB write delay).
    Kept as a standalone function so it can be unit tested without Redis.
    """
    print(f"Processing Order ID: {order['order_id']} for Item: {order['item_name']}...", flush=True)
    time.sleep(2)
    print(f"Successfully processed Order ID: {order['order_id']}", flush=True)


def run_worker_loop(redis_client) -> None:
    """Main blocking loop: pulls orders from the Redis queue and processes them."""
    print("Worker started. Listening for orders in queue...", flush=True)
    while True:
        try:
            # Blocking pop with a timeout so the loop can stay responsive
            result = redis_client.blpop("order_queue", timeout=5)

            # None means the timeout was hit with no new order — just retry
            if result is None:
                continue

            _, order_data_json = result
            if order_data_json:
                order = json.loads(order_data_json)
                process_order(order)
        except Exception as e:
            print(f"Error processing order: {e}", flush=True)
            time.sleep(2)


if __name__ == "__main__":
    # Only start the Redis connection and the loop when run directly,
    # not when imported (e.g. during tests or CI).
    client = get_redis_client()
    run_worker_loop(client)
