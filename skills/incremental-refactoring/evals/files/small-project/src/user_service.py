"""User service module - intentionally complex for refactoring eval."""

import re
import json
from datetime import datetime


def validate_and_create_user(data, db, email_service, logger):
    """Validate user data and create user - high cyclomatic complexity."""
    errors = []

    # Name validation
    if not data.get("name"):
        errors.append("Name is required")
    elif len(data["name"]) < 2:
        errors.append("Name must be at least 2 characters")
    elif len(data["name"]) > 100:
        errors.append("Name must be at most 100 characters")
    elif not re.match(r"^[a-zA-Z\s\-']+$", data["name"]):
        errors.append("Name contains invalid characters")

    # Email validation
    if not data.get("email"):
        errors.append("Email is required")
    elif not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", data["email"]):
        errors.append("Invalid email format")
    else:
        existing = db.find_user_by_email(data["email"])
        if existing:
            errors.append("Email already registered")

    # Password validation
    if not data.get("password"):
        errors.append("Password is required")
    elif len(data["password"]) < 8:
        errors.append("Password must be at least 8 characters")
    elif len(data["password"]) > 128:
        errors.append("Password too long")
    elif not re.search(r"[A-Z]", data["password"]):
        errors.append("Password must contain uppercase letter")
    elif not re.search(r"[a-z]", data["password"]):
        errors.append("Password must contain lowercase letter")
    elif not re.search(r"[0-9]", data["password"]):
        errors.append("Password must contain a number")
    elif not re.search(r"[!@#$%^&*]", data["password"]):
        errors.append("Password must contain a special character")

    # Age validation
    if data.get("age") is not None:
        if not isinstance(data["age"], int):
            errors.append("Age must be an integer")
        elif data["age"] < 0:
            errors.append("Age cannot be negative")
        elif data["age"] > 150:
            errors.append("Age seems invalid")

    # Phone validation
    if data.get("phone"):
        phone = re.sub(r"[\s\-\(\)]", "", data["phone"])
        if not re.match(r"^\+?[0-9]{10,15}$", phone):
            errors.append("Invalid phone number")

    # Address validation
    if data.get("address"):
        addr = data["address"]
        if not addr.get("street"):
            errors.append("Street is required in address")
        if not addr.get("city"):
            errors.append("City is required in address")
        if not addr.get("zip"):
            errors.append("ZIP code is required in address")
        elif not re.match(r"^\d{5}(-\d{4})?$", addr["zip"]):
            errors.append("Invalid ZIP code format")

    if errors:
        logger.warn(f"Validation failed: {errors}")
        return {"success": False, "errors": errors}

    # Create user
    try:
        hashed_pw = _hash_password(data["password"])
        user = db.create_user({
            "name": data["name"],
            "email": data["email"],
            "password": hashed_pw,
            "age": data.get("age"),
            "phone": data.get("phone"),
            "address": data.get("address"),
            "created_at": datetime.now().isoformat(),
        })
        logger.info(f"User created: {user['id']}")

        # Send welcome email
        try:
            email_service.send_welcome(user["email"], user["name"])
        except Exception as e:
            logger.error(f"Failed to send welcome email: {e}")

        return {"success": True, "user": user}
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        return {"success": False, "errors": ["Internal error"]}


def format_user_for_api(user):
    """Format user data for API response - duplicated logic."""
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "age": user.get("age"),
        "phone": user.get("phone"),
        "address": _format_address(user.get("address")),
        "created_at": user.get("created_at"),
        "display_name": f"{user['name']} <{user['email']}>",
    }


def format_user_for_admin(user):
    """Format user data for admin panel - duplicated with format_user_for_api."""
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "age": user.get("age"),
        "phone": user.get("phone"),
        "address": _format_address(user.get("address")),
        "created_at": user.get("created_at"),
        "display_name": f"{user['name']} <{user['email']}>",
        "is_admin": user.get("is_admin", False),
        "last_login": user.get("last_login"),
    }


def format_user_for_export(user):
    """Format user data for CSV export - duplicated with format_user_for_api."""
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "age": user.get("age"),
        "phone": user.get("phone"),
        "address": _format_address(user.get("address")),
        "created_at": user.get("created_at"),
        "display_name": f"{user['name']} <{user['email']}>",
        "export_date": datetime.now().isoformat(),
    }


def _format_address(address):
    if not address:
        return None
    return f"{address.get('street', '')}, {address.get('city', '')}, {address.get('zip', '')}"


def _hash_password(password):
    """Stub for password hashing."""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()
