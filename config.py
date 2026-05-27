"""Shared local configuration helpers for Milicia."""

import json
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DATA_FILE = os.path.join(BASE_DIR, "user_data.json")


def load_user_data() -> dict:
    """Load user_data.json without forcing callers to handle missing/bad files."""
    if not os.path.exists(USER_DATA_FILE):
        return {}

    try:
        with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def get_user_name(default: str = "pengguna") -> str:
    name = load_user_data().get("name")
    if isinstance(name, str) and name.strip():
        return name.strip()
    return default


def get_gemini_api_key() -> str | None:
    api_key = load_user_data().get("gemini_api_key")
    if isinstance(api_key, str) and api_key.strip():
        return api_key.strip()
    return None


def get_local_stt_enabled(default: bool = True) -> bool:
    value = load_user_data().get("local_stt_enabled", default)
    return bool(value)


def get_local_stt_model(default: str = "base") -> str:
    model = load_user_data().get("local_stt_model", default)
    if isinstance(model, str) and model.strip():
        return model.strip()
    return default


def get_local_stt_device(default: str = "auto") -> str:
    device = load_user_data().get("local_stt_device", default)
    if isinstance(device, str) and device.strip():
        return device.strip()
    return default


def get_local_stt_compute_type(default: str = "int8") -> str:
    compute_type = load_user_data().get("local_stt_compute_type", default)
    if isinstance(compute_type, str) and compute_type.strip():
        return compute_type.strip()
    return default
