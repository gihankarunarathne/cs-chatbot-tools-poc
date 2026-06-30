from datetime import date

from ..models.tools import OrderInfo, ProductInfo, RefundInfo, ReturnEligibility, WarrantyInfo

_ORDERS: dict[str, OrderInfo] = {
    "NXY-1001": OrderInfo(
        order_id="NXY-1001",
        status="in_transit",
        items=["Samsung Galaxy S24", "Phone Case"],
        eta=date(2026, 7, 2),
        carrier="Aramex",
    ),
    "NXY-2002": OrderInfo(
        order_id="NXY-2002",
        status="delivered",
        items=["Sony WH-1000XM5 Headphones"],
        eta=None,
        carrier="DHL",
    ),
    "NXY-3003": OrderInfo(
        order_id="NXY-3003",
        status="processing",
        items=["Nike Air Max 270", "Adidas Socks"],
        eta=date(2026, 7, 5),
        carrier=None,
    ),
    "NXY-4004": OrderInfo(
        order_id="NXY-4004",
        status="cancelled",
        items=["Apple AirPods Pro"],
        eta=None,
        carrier=None,
    ),
}

_REFUNDS: dict[str, RefundInfo] = {
    "NXY-2002": RefundInfo(
        order_id="NXY-2002",
        refund_status="approved",
        amount=450.0,
        currency="AED",
        eta_days=3,
    ),
    "NXY-4004": RefundInfo(
        order_id="NXY-4004",
        refund_status="processed",
        amount=199.0,
        currency="AED",
        eta_days=None,
    ),
}

_WARRANTIES: dict[str, WarrantyInfo] = {
    "PRD-A": WarrantyInfo(
        product_id="PRD-A",
        in_warranty=True,
        expires_on=date(2026, 12, 31),
        coverage="Manufacturing defects, hardware failures",
    ),
    "PRD-B": WarrantyInfo(
        product_id="PRD-B",
        in_warranty=False,
        expires_on=date(2025, 6, 1),
        coverage=None,
    ),
    "PRD-GALAXY-S24": WarrantyInfo(
        product_id="PRD-GALAXY-S24",
        in_warranty=True,
        expires_on=date(2027, 3, 15),
        coverage="Full manufacturer warranty",
    ),
}

_PRODUCTS: dict[str, ProductInfo] = {
    "PRD-A": ProductInfo(product_id="PRD-A", name="Samsung Galaxy S24", price=2999.0, in_stock=True),
    "PRD-B": ProductInfo(product_id="PRD-B", name="Sony WH-1000XM5", price=1299.0, in_stock=False),
    "PRD-C": ProductInfo(product_id="PRD-C", name="Nike Air Max 270", price=549.0, in_stock=True),
}


def lookup_order(order_id: str) -> OrderInfo:
    return _ORDERS.get(order_id.upper(), OrderInfo(
        order_id=order_id, status="unknown", items=[], found=False
    ))


def check_refund_status(order_id: str) -> RefundInfo:
    return _REFUNDS.get(order_id.upper(), RefundInfo(
        order_id=order_id, refund_status="none", found=True
    ))


def check_warranty(product_id: str) -> WarrantyInfo:
    return _WARRANTIES.get(product_id.upper(), WarrantyInfo(
        product_id=product_id, in_warranty=False, found=False
    ))


def check_return_eligibility(order_id: str) -> ReturnEligibility:
    order = _ORDERS.get(order_id.upper())
    if not order:
        return ReturnEligibility(order_id=order_id, eligible=False, window_days=0, reason="Order not found", found=False)
    if order.status == "delivered":
        return ReturnEligibility(order_id=order_id, eligible=True, window_days=14, reason="Within return window")
    if order.status == "cancelled":
        return ReturnEligibility(order_id=order_id, eligible=False, window_days=0, reason="Order was cancelled")
    return ReturnEligibility(order_id=order_id, eligible=False, window_days=0, reason="Order not yet delivered")


def lookup_product(product_id: str) -> ProductInfo:
    return _PRODUCTS.get(product_id.upper(), ProductInfo(
        product_id=product_id, name="Unknown", price=0.0, in_stock=False, found=False
    ))
