"""Tests for user_service - covers main paths for Gate B."""

import pytest
from unittest.mock import MagicMock
from src.user_service import validate_and_create_user, format_user_for_api


class TestValidateAndCreateUser:
    def setup_method(self):
        self.db = MagicMock()
        self.email_service = MagicMock()
        self.logger = MagicMock()
        self.valid_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "password": "Secure1!pass",
        }
        self.db.find_user_by_email.return_value = None
        self.db.create_user.return_value = {
            "id": "user-1",
            "name": "John Doe",
            "email": "john@example.com",
        }

    def test_valid_user_creation(self):
        result = validate_and_create_user(self.valid_data, self.db, self.email_service, self.logger)
        assert result["success"] is True
        assert result["user"]["id"] == "user-1"

    def test_missing_name(self):
        self.valid_data.pop("name")
        result = validate_and_create_user(self.valid_data, self.db, self.email_service, self.logger)
        assert result["success"] is False
        assert "Name is required" in result["errors"]

    def test_missing_email(self):
        self.valid_data.pop("email")
        result = validate_and_create_user(self.valid_data, self.db, self.email_service, self.logger)
        assert result["success"] is False
        assert "Email is required" in result["errors"]

    def test_duplicate_email(self):
        self.db.find_user_by_email.return_value = {"id": "existing"}
        result = validate_and_create_user(self.valid_data, self.db, self.email_service, self.logger)
        assert result["success"] is False
        assert "Email already registered" in result["errors"]

    def test_short_password(self):
        self.valid_data["password"] = "Ab1!"
        result = validate_and_create_user(self.valid_data, self.db, self.email_service, self.logger)
        assert result["success"] is False

    def test_db_error(self):
        self.db.create_user.side_effect = Exception("DB error")
        result = validate_and_create_user(self.valid_data, self.db, self.email_service, self.logger)
        assert result["success"] is False

    def test_email_send_failure_still_succeeds(self):
        self.email_service.send_welcome.side_effect = Exception("SMTP error")
        result = validate_and_create_user(self.valid_data, self.db, self.email_service, self.logger)
        assert result["success"] is True


class TestFormatUserForApi:
    def test_basic_format(self):
        user = {"id": "1", "name": "Jane", "email": "jane@example.com"}
        result = format_user_for_api(user)
        assert result["id"] == "1"
        assert result["display_name"] == "Jane <jane@example.com>"
