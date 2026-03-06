"""Order processing module - intentionally coupled for refactoring eval."""

from datetime import datetime


def process_order(order_data, db, inventory, payment, shipping, logger):
    """Process an order - high coupling and complexity."""

    # Validate order
    if not order_data.get("items"):
        return {"success": False, "error": "No items in order"}
    if not order_data.get("user_id"):
        return {"success": False, "error": "User ID required"}
    if not order_data.get("payment_method"):
        return {"success": False, "error": "Payment method required"}

    user = db.find_user(order_data["user_id"])
    if not user:
        return {"success": False, "error": "User not found"}

    # Calculate totals
    subtotal = 0
    for item in order_data["items"]:
        product = inventory.get_product(item["product_id"])
        if not product:
            return {"success": False, "error": f"Product {item['product_id']} not found"}
        if product["stock"] < item["quantity"]:
            return {"success": False, "error": f"Insufficient stock for {product['name']}"}
        item_total = product["price"] * item["quantity"]
        if item.get("discount_percent"):
            item_total *= (1 - item["discount_percent"] / 100)
        subtotal += item_total

    # Apply order-level discount
    if order_data.get("coupon_code"):
        coupon = db.find_coupon(order_data["coupon_code"])
        if coupon and coupon["valid_until"] > datetime.now().isoformat():
            if coupon["type"] == "percent":
                subtotal *= (1 - coupon["value"] / 100)
            elif coupon["type"] == "fixed":
                subtotal -= coupon["value"]

    tax = subtotal * 0.08
    shipping_cost = _calculate_shipping(order_data, shipping)
    total = subtotal + tax + shipping_cost

    # Process payment
    payment_result = payment.charge(
        user_id=user["id"],
        amount=total,
        method=order_data["payment_method"],
    )
    if not payment_result["success"]:
        logger.error(f"Payment failed: {payment_result.get('error')}")
        return {"success": False, "error": "Payment failed"}

    # Reserve inventory
    for item in order_data["items"]:
        inventory.reserve(item["product_id"], item["quantity"])

    # Create order record
    order = db.create_order({
        "user_id": user["id"],
        "items": order_data["items"],
        "subtotal": subtotal,
        "tax": tax,
        "shipping_cost": shipping_cost,
        "total": total,
        "payment_id": payment_result["payment_id"],
        "status": "confirmed",
        "created_at": datetime.now().isoformat(),
    })

    logger.info(f"Order created: {order['id']}")
    return {"success": True, "order": order}


def _calculate_shipping(order_data, shipping):
    """Calculate shipping cost - could be extracted."""
    address = order_data.get("shipping_address", {})
    total_weight = sum(item.get("weight", 0) * item["quantity"] for item in order_data["items"])

    if total_weight == 0:
        return 0

    rate = shipping.get_rate(
        zip_code=address.get("zip", ""),
        weight=total_weight,
    )
    return rate.get("cost", 5.99)
