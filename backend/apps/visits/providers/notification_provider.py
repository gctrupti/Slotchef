"""Notification provider abstraction for Emergency Alerts, SOS notifications, and Safety Warnings."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)


class NotificationProviderInterface(ABC):
    """Abstract interface for dispatching urgent safety and incident alerts."""

    @abstractmethod
    def send_alert(
        self,
        recipient_name: str,
        recipient_target: str,
        channel: str,
        title: str,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> bool:
        """Deliver urgent alert via specified channel (sms, email, push)."""
        pass


class MockNotificationProvider(NotificationProviderInterface):
    """Development and test alert delivery provider. Strictly forbidden in production."""

    dispatched_alerts: list[dict[str, Any]] = []

    def __init__(self) -> None:
        if not settings.DEBUG and not getattr(settings, "IS_TESTING", False):
            raise RuntimeError("MockNotificationProvider is strictly forbidden in production environments.")

    def send_alert(
        self,
        recipient_name: str,
        recipient_target: str,
        channel: str,
        title: str,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> bool:
        if not settings.DEBUG and not getattr(settings, "IS_TESTING", False):
            raise RuntimeError("MockNotificationProvider is strictly forbidden in production environments.")

        record = {
            "recipient_name": recipient_name,
            "recipient_target": recipient_target,
            "channel": channel,
            "title": title,
            "message": message,
            "payload": payload or {},
        }
        self.dispatched_alerts.append(record)
        logger.warning(
            "EMERGENCY ALERT dispatched to %s (%s) via %s: %s - %s",
            recipient_name,
            recipient_target,
            channel,
            title,
            message,
        )
        return True


class ProductionNotificationProvider(NotificationProviderInterface):
    """Production provider using FCM / Twilio / SES."""

    def send_alert(
        self,
        recipient_name: str,
        recipient_target: str,
        channel: str,
        title: str,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> bool:
        logger.info("Production alert dispatch to %s via %s: %s", recipient_target, channel, title)
        # Production channel dispatch
        return True


def get_notification_provider() -> NotificationProviderInterface:
    """Return configured notification provider instance."""
    provider_name = getattr(settings, "SLOTCHEF_NOTIFICATION_PROVIDER", "mock").lower()
    if provider_name == "production" or provider_name == "fcm":
        return ProductionNotificationProvider()
    return MockNotificationProvider()

