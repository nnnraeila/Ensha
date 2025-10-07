# backend/otp.py
"""
OTP (One-Time Password) manager.

Handles:
- Generation of OTP codes
- Storage in DB with expiry
- Secure delivery to user via Telegram
- Validation & marking as used
- Audit logging and DR reporting

Dependencies:
- backend.db (for create_otp_record, get_valid_otp, mark_otp_used, add_log, get_user, record_dr_event)
- backend.alerts (send_alert)
- config.settings (OTP_LENGTH, OTP_EXPIRY_SECONDS)
"""

import random
import traceback
from datetime import datetime, timedelta

from config import settings
from backend import db
from backend import alerts

# Defaults if not defined in settings
OTP_LENGTH = getattr(settings, "OTP_LENGTH", 6)
OTP_EXPIRY_SECONDS = getattr(settings, "OTP_EXPIRY_SECONDS", 300)  # 5 minutes


# -----------------------
# Helpers
# -----------------------
def _generate_code(length: int = OTP_LENGTH) -> str:
    """Generate numeric OTP code of given length."""
    return ''.join(str(random.randint(0, 9)) for _ in range(length))


# -----------------------
# API
# -----------------------
def request(user_id: int, purpose: str = "restore") -> dict:
    """
    Generate and send OTP to a user via Telegram.
    Args:
        user_id: ID of user requesting OTP
        purpose: string (e.g., "restore", "snapshot", "admin")
    Returns:
        {ok: bool, message: str, code?: str (if debug mode)}
    """
    try:
        user = db.get_user(user_id)
        if not user:
            return {"ok": False, "message": "User not found"}

        code = _generate_code()
        expiry = datetime.utcnow() + timedelta(seconds=OTP_EXPIRY_SECONDS)
        otp = db.create_otp_record(user_id, code, expiry)

        # Prepare message
        msg = (
            f"🔐 OTP for {purpose}\n\n"
            f"Code: {code}\n"
            f"Valid for {OTP_EXPIRY_SECONDS // 60} minutes."
        )

        # Deliver via Telegram
        sent = False
        try:
            sent = alerts.send_alert(user.telegram_chat_id, msg)
        except Exception:
            db.add_log(user_id, "otp_alert_error", traceback.format_exc())

        # Log
        db.add_log(user_id, "otp_requested", f"OTP {otp.id} for {purpose}, sent={sent}")
        db.record_dr_event(user_id, "otp_issued", f"OTP {otp.id} issued for {purpose}, expires={expiry.isoformat()}")

        if not sent:
            return {"ok": False, "message": "Failed to deliver OTP via Telegram."}

        if getattr(settings, "DEBUG_SHOW_OTP", False):
            return {"ok": True, "message": "OTP sent via Telegram", "code": code}
        return {"ok": True, "message": "OTP sent via Telegram"}

    except Exception as e:
        db.add_log(user_id, "otp_request_error", traceback.format_exc())
        db.record_dr_event(user_id, "otp_request_failed", traceback.format_exc())
        return {"ok": False, "message": "Unexpected error while generating OTP"}


def verify(user_id: int, code: str, purpose: str = "restore") -> dict:
    """
    Verify OTP for a user.
    Marks OTP as used if valid.
    Args:
        user_id: user who owns OTP
        code: entered OTP code
        purpose: context of OTP
    Returns:
        {ok: bool, message: str}
    """
    try:
        otp = db.get_valid_otp(user_id, code)
        if not otp:
            db.add_log(user_id, "otp_invalid", f"Purpose={purpose}, code={code}")
            return {"ok": False, "message": "Invalid or expired OTP"}

        db.mark_otp_used(otp.id)
        db.add_log(user_id, "otp_verified", f"Purpose={purpose}, OTP {otp.id} used")
        db.record_dr_event(user_id, "otp_used", f"OTP {otp.id} used for {purpose}")
        return {"ok": True, "message": "OTP verified successfully"}

    except Exception as e:
        db.add_log(user_id, "otp_verify_error", traceback.format_exc())
        db.record_dr_event(user_id, "otp_verify_failed", traceback.format_exc())
        return {"ok": False, "message": "Unexpected error while verifying OTP"}
