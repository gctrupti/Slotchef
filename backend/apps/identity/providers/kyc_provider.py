"""Identity and background verification (KYC/BGV) provider abstraction."""

from __future__ import annotations

import logging
import uuid
from abc import ABC, abstractmethod
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)


class KYCProviderInterface(ABC):
    """Abstract interface for government ID verification and criminal background check."""

    @abstractmethod
    def verify_identity(self, doc_type: str, masked_doc_number: str, full_doc_number: str = "") -> dict[str, Any]:
        """Verify government document validity with provider."""
        pass

    @abstractmethod
    def run_background_check(self, candidate_details: dict[str, Any]) -> dict[str, Any]:
        """Initiate background verification (court records, police verification)."""
        pass


class MockKYCProvider(KYCProviderInterface):
    """Development and testing mock KYC provider. Never used in production."""

    def __init__(self) -> None:
        if not settings.DEBUG and not getattr(settings, "IS_TESTING", False):
            raise RuntimeError("MockKYCProvider is strictly forbidden in production environments.")

    def verify_identity(self, doc_type: str, masked_doc_number: str, full_doc_number: str = "") -> dict[str, Any]:
        if not settings.DEBUG and not getattr(settings, "IS_TESTING", False):
            raise RuntimeError("MockKYCProvider is strictly forbidden in production environments.")

        return {
            "success": True,
            "document_type": doc_type,
            "masked_number": masked_doc_number,
            "status": "verified",
            "provider_ref": f"mock_doc_{uuid.uuid4().hex[:10]}",
        }

    def run_background_check(self, candidate_details: dict[str, Any]) -> dict[str, Any]:
        if not settings.DEBUG and not getattr(settings, "IS_TESTING", False):
            raise RuntimeError("MockKYCProvider is strictly forbidden in production environments.")

        return {
            "status": "clear",
            "partner": "MockTrustBGV",
            "reference": f"bgv_ref_{uuid.uuid4().hex[:12]}",
            "risk_score": 0.05,
            "records_found": 0,
        }


class ProductionKYCProvider(KYCProviderInterface):
    """Integration for verified third-party background and identity checks (e.g. IDfy / AuthBridge)."""

    def __init__(self) -> None:
        self.api_key = getattr(settings, "KYC_PROVIDER_API_KEY", "")
        self.endpoint = getattr(settings, "KYC_PROVIDER_ENDPOINT", "")

    def verify_identity(self, doc_type: str, masked_doc_number: str, full_doc_number: str = "") -> dict[str, Any]:
        if not self.api_key or not self.endpoint:
            logger.error("KYC provider credentials not configured in production.")
            return {"success": False, "status": "pending", "error": "Provider not configured"}
        # Staged external KYC API call
        return {"success": True, "status": "pending", "provider_ref": "ext_kyc_pending"}

    def run_background_check(self, candidate_details: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key or not self.endpoint:
            logger.error("KYC provider credentials not configured in production.")
            return {"status": "pending", "error": "Provider not configured"}
        return {"status": "pending", "partner": "ProductionBGV", "reference": "ext_bgv_pending"}


def get_kyc_provider() -> KYCProviderInterface:
    """Return configured KYC provider instance."""
    provider_name = getattr(settings, "SLOTCHEF_KYC_PROVIDER", "mock").lower()
    if provider_name == "production" or provider_name == "idfy":
        return ProductionKYCProvider()
    return MockKYCProvider()

