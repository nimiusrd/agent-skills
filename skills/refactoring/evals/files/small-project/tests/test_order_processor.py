"""Tests for order_processor - covers main paths for Gate B."""

import pytest
from unittest.mock import MagicMock
from src.order_processor import process_order


class TestProcessOrder:
    def setup_method(self):
        self.db = MagicMock()
        self.inventory = MagicMock()
        self.payment = MagicMock()
        self.shipping = MagicMock()
        self.logger = MagicMock()

        self.db.find_user.return_value = {"id": "user-1", "name": "John"}
        self.inventory.get_product.return_value = {"name": "Widget", "price": 10.0, "stock": 100}
        self.payment.charge.return_value = {"success": True, "payment_id": "pay-1"}
        self.shipping.get_rate.return_value = {"cost": 5.99}
        self.db.create_order.return_value = {"id": "order-1"}

        self.valid_order = {
            "user_id": "user-1",
            "items": [{"product_id": "prod-1", "quantity": 2}],
            "payment_method": "credit_card",
            "shipping_address": {"zip": "12345"},
        }

    def test_successful_order(self):
        result = process_order(self.valid_order, self.db, self.inventory, self.payment, self.shipping, self.logger)
        assert result["success"] is True

    def test_no_items(self):
        self.valid_order["items"] = []
        result = process_order(self.valid_order, self.db, self.inventory, self.payment, self.shipping, self.logger)
        assert result["success"] is False

    def test_user_not_found(self):
        self.db.find_user.return_value = None
        result = process_order(self.valid_order, self.db, self.inventory, self.payment, self.shipping, self.logger)
        assert result["success"] is False

    def test_payment_failure(self):
        self.payment.charge.return_value = {"success": False, "error": "Declined"}
        result = process_order(self.valid_order, self.db, self.inventory, self.payment, self.shipping, self.logger)
        assert result["success"] is False

    def test_insufficient_stock(self):
        self.inventory.get_product.return_value = {"name": "Widget", "price": 10.0, "stock": 0}
        result = process_order(self.valid_order, self.db, self.inventory, self.payment, self.shipping, self.logger)
        assert result["success"] is False
