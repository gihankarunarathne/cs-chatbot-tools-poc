from datetime import date

from pydantic import BaseModel


class OrderInfo(BaseModel):
    order_id: str
    status: str
    items: list[str]
    eta: date | None = None
    carrier: str | None = None
    found: bool = True


class RefundInfo(BaseModel):
    order_id: str
    refund_status: str
    amount: float | None = None
    currency: str = "AED"
    eta_days: int | None = None
    found: bool = True


class WarrantyInfo(BaseModel):
    product_id: str
    in_warranty: bool
    expires_on: date | None = None
    coverage: str | None = None
    found: bool = True


class ReturnEligibility(BaseModel):
    order_id: str
    eligible: bool
    window_days: int
    reason: str
    found: bool = True


class ProductInfo(BaseModel):
    product_id: str
    name: str
    price: float
    currency: str = "AED"
    in_stock: bool
    found: bool = True
