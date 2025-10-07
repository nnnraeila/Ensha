"""
alerts.py
---------
Central alert manager for sending OTPs and system alerts
to Telegram (or other channels in the future).

Dependencies:
    - python-telegram-bot (pip install python-telegram-bot==20.3)
    - config/settings.py for credentials

Author: Your Name
"""

import logging
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError

from config import settings

logger = logging.getLogger("alerts")
logger.setLevel(logging.INFO)


class AlertManager:
    def __init__(self):
        self.bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
        self.chat_id = getattr(settings, "TELEGRAM_CHAT_ID", None)

        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram not configured. Alerts will be disabled.")
            self.bot = None
        else:
            try:
                self.bot = Bot(token=self.bot_token)
                logger.info("Telegram bot initialized")
            except TelegramError as e:
                logger.error(f"Failed to init Telegram bot: {e}")
                self.bot = None

    def send_message(self, message: str) -> bool:
        """
        Send a plain text message to Telegram.
        Returns True if success, False if failure.
        """
        if not self.bot:
            logger.debug(f"Alert skipped (no bot): {message}")
            return False

        try:
            self.bot.send_message(chat_id=self.chat_id, text=message)
            return True
        except TelegramError as e:
            logger.error(f"Telegram send_message error: {e}")
            return False

    def send_otp(self, otp: str) -> bool:
        """
        Send OTP securely to user via Telegram.
        """
        message = f"Your Secure Backup OTP: {otp}\n\nThis code expires in {settings.OTP_EXPIRY_SECONDS//60} minutes."
        return self.send_message(message)

    def send_backup_alert(self, filename: str, status: str, version: int = None) -> bool:
        """
        Notify user of backup events (success/failure).
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if status.lower() == "success":
            msg = f"Backup Success\nFile: {filename}\nVersion: {version}\nTime: {now}"
        else:
            msg = f"Backup Failed\nFile: {filename}\nTime: {now}"

        return self.send_message(msg)

    def send_deletion_alert(self, filename: str, deleted_at: str = None) -> bool:
        """
        Alert user when a monitored file is deleted.
        """
        when = deleted_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = f"File Deletion Detected!\nFile: {filename}\nDeleted at: {when}"
        return self.send_message(msg)

    def send_recovery_alert(self, filename: str, version: int, status: str) -> bool:
        """
        Notify user when a file is restored.
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if status.lower() == "success":
            msg = f"File Restored Successfully\nFile: {filename}\nVersion: {version}\nTime: {now}"
        else:
            msg = f"File Restore Failed\nFile: {filename}\nVersion: {version}\nTime: {now}"

        return self.send_message(msg)


# Singleton instance (can be imported anywhere)
alert_manager = AlertManager()
