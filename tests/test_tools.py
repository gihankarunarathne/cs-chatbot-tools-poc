from cschatbot.tools.mocks import (
    check_refund_status,
    check_return_eligibility,
    check_warranty,
    lookup_order,
    lookup_product,
)


def test_lookup_order_known():
    result = lookup_order("NXY-1001")
    assert result.found is True
    assert result.status == "in_transit"
    assert result.carrier == "Aramex"


def test_lookup_order_delivered():
    result = lookup_order("NXY-2002")
    assert result.found is True
    assert result.status == "delivered"


def test_lookup_order_unknown():
    result = lookup_order("NXY-9999")
    assert result.found is False
    assert result.status == "unknown"


def test_lookup_order_case_insensitive():
    result = lookup_order("nxy-1001")
    assert result.found is True


def test_check_refund_known():
    result = check_refund_status("NXY-2002")
    assert result.refund_status == "approved"
    assert result.amount == 450.0
    assert result.currency == "AED"


def test_check_refund_none():
    result = check_refund_status("NXY-1001")
    assert result.refund_status == "none"


def test_check_warranty_in_warranty():
    result = check_warranty("PRD-A")
    assert result.in_warranty is True
    assert result.found is True


def test_check_warranty_expired():
    result = check_warranty("PRD-B")
    assert result.in_warranty is False


def test_check_warranty_unknown():
    result = check_warranty("PRD-UNKNOWN")
    assert result.found is False


def test_return_eligibility_delivered():
    result = check_return_eligibility("NXY-2002")
    assert result.eligible is True
    assert result.window_days == 14


def test_return_eligibility_in_transit():
    result = check_return_eligibility("NXY-1001")
    assert result.eligible is False


def test_return_eligibility_unknown():
    result = check_return_eligibility("NXY-9999")
    assert result.found is False
    assert result.eligible is False


def test_lookup_product_known():
    result = lookup_product("PRD-A")
    assert result.found is True
    assert result.in_stock is True


def test_lookup_product_unknown():
    result = lookup_product("PRD-NOPE")
    assert result.found is False
