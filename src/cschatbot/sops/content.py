SOP_LIBRARY: dict[str, str] = {
    "order_tracking": """\
ORDER TRACKING SOP
1. Confirm the order ID. If status is in_transit, share carrier + ETA.
2. If delivered but customer says not received, advise to check with neighbors/concierge,
   then offer to open an investigation (24-48h).
3. If processing, explain it ships within 1-2 business days.
4. Never invent tracking numbers. If order not found, ask the customer to re-check the ID.""",

    "refund": """\
REFUND SOP
1. Verify order + refund eligibility (delivered/cancelled orders only).
2. State current refund_status plainly. If 'processed', refunds reach the card in 5-7 business days.
3. If 'none' and customer is eligible, explain how to initiate (within 14 days of delivery).
4. Always give amount + currency when available.""",

    "warranty": """\
WARRANTY SOP
1. Check warranty coverage for the product.
2. If in_warranty, explain claim steps: upload invoice + defect photos via the app.
3. If expired, state expiry date and offer paid repair options.
4. Do not promise replacement before inspection.""",

    "return": """\
RETURN SOP
1. Check return eligibility (standard window 14 days, some categories excluded).
2. If eligible, explain pickup scheduling and refund-after-inspection policy.
3. If outside window, decline politely and mention exception escalation.""",

    "product_info": """\
PRODUCT INFO SOP
1. Share name, price, stock status from the catalog.
2. Do not speculate on specs not returned by the tool.""",

    "general": """\
GENERAL QUERY SOP
Answer concisely from known Noon policy. If unsure, offer to connect to a human agent.""",

    "handover": """\
HANDOVER SOP
Apologize, explain this needs a human specialist, and confirm a CS agent will follow up within 24 hours.""",
}
