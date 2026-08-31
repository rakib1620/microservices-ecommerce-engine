from worker import process_order, get_redis_client


def test_worker_module_loads():
    """Importing worker.py should not start the infinite loop or connect to Redis —
    it should just expose the functions."""
    assert callable(process_order)
    assert callable(get_redis_client)


def test_process_order_runs(capsys):
    """process_order() should run standalone, without a live Redis connection,
    and print the expected status messages."""
    fake_order = {"order_id": 123, "item_name": "Test Item"}
    process_order(fake_order)
    captured = capsys.readouterr()
    assert "Processing Order ID: 123" in captured.out
    assert "Successfully processed Order ID: 123" in captured.out
