from src.service import sync_orders


def test_sync_orders_smoke() -> None:
    assert sync_orders() is None
