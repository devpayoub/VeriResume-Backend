import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def log_credit_request(user, message: str):
    logger.info(f"CREDIT REQUEST from {user.email}: {message}")


def log_credit_added(user, amount: int, admin_note: str = ''):
    logger.info(f"CREDITS ADDED to {user.email}: {amount} credits. Note: {admin_note}")
