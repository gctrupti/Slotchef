"""REST API views for Pricing rules, Platform commission, and Price breakdown snapshots."""

from __future__ import annotations

from typing import Any

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bookings.models import Booking, HouseholdPackageSubscription
from apps.communities.models import Society
from apps.cooks.models import CookProfile
from apps.finance.models import (
    CommissionLedger,
    PaymentTransaction,
    PlatformCommissionConfig,
    ServicePricingRule,
)
from apps.finance.serializers import (
    BookingPriceBreakdownSerializer,
    CashCollectionRecordSerializer,
    CashDisputeRequestSerializer,
    CashReportRequestSerializer,
    CashResolveRequestSerializer,
    CommissionLedgerSerializer,
    CookFinancialSummarySerializer,
    CookPayoutCreateRequestSerializer,
    CookPayoutRecordSerializer,
    PaymentOrderCreateRequestSerializer,
    PaymentOrderSerializer,
    PaymentTransactionSerializer,
    PaymentVerifyRequestSerializer,
    PlatformCommissionConfigSerializer,
    PriceEstimateRequestSerializer,
    PriceEstimateResponseSerializer,
    RefundRecordSerializer,
    RefundRequestSerializer,
    ServicePricingRuleSerializer,
)
from apps.finance.services.cash_service import CashService
from apps.finance.services.payment_service import PaymentService
from apps.finance.services.payout_service import PayoutService
from apps.finance.services.pricing_calculator import PricingCalculatorService
from apps.identity.models import Role
from apps.identity.permissions import IsCook, IsPlatformAdmin, IsSocietyAdmin


class ServicePricingRuleListCreateView(APIView):
    """List active pricing rules or create new pricing tier."""

    def get_permissions(self) -> list[Any]:
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), (IsPlatformAdmin | IsSocietyAdmin)()]
        return [permissions.IsAuthenticated()]

    @extend_schema(
        responses={200: ServicePricingRuleSerializer(many=True)},
        summary="List active pricing rules",
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        qs = ServicePricingRule.objects.filter(is_active=True).select_related("society")
        society_id = request.query_params.get("society_id")
        if society_id:
            qs = qs.filter(society_id=society_id)
        pricing_type = request.query_params.get("pricing_type")
        if pricing_type:
            qs = qs.filter(pricing_type=pricing_type)

        serializer = ServicePricingRuleSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=ServicePricingRuleSerializer,
        responses={201: ServicePricingRuleSerializer},
        summary="Create a new service pricing rule (Admin only)",
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = ServicePricingRuleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rule = serializer.save()
        return Response(ServicePricingRuleSerializer(rule).data, status=status.HTTP_201_CREATED)


class ServicePricingRuleDetailView(APIView):
    """Retrieve or update a specific pricing rule."""

    def get_permissions(self) -> list[Any]:
        if self.request.method in ["PATCH", "PUT", "DELETE"]:
            return [permissions.IsAuthenticated(), (IsPlatformAdmin | IsSocietyAdmin)()]
        return [permissions.IsAuthenticated()]

    @extend_schema(
        responses={200: ServicePricingRuleSerializer},
        summary="Retrieve pricing rule details",
    )
    def get(self, request: Request, rule_id: str, *args: Any, **kwargs: Any) -> Response:
        rule = get_object_or_404(ServicePricingRule, id=rule_id)
        return Response(ServicePricingRuleSerializer(rule).data, status=status.HTTP_200_OK)

    @extend_schema(
        request=ServicePricingRuleSerializer,
        responses={200: ServicePricingRuleSerializer},
        summary="Update a pricing rule (Admin only)",
    )
    def patch(self, request: Request, rule_id: str, *args: Any, **kwargs: Any) -> Response:
        rule = get_object_or_404(ServicePricingRule, id=rule_id)
        serializer = ServicePricingRuleSerializer(rule, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        return Response(ServicePricingRuleSerializer(updated).data, status=status.HTTP_200_OK)


class PlatformCommissionConfigView(APIView):
    """Retrieve or configure platform commission rates (Admin only)."""

    permission_classes = [permissions.IsAuthenticated, (IsPlatformAdmin | IsSocietyAdmin)]

    @extend_schema(
        responses={200: PlatformCommissionConfigSerializer(many=True)},
        summary="List platform commission policies (Admin only)",
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        configs = PlatformCommissionConfig.objects.filter(is_active=True).select_related("society")
        society_id = request.query_params.get("society_id")
        if society_id:
            configs = configs.filter(society_id=society_id)
        serializer = PlatformCommissionConfigSerializer(configs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=PlatformCommissionConfigSerializer,
        responses={201: PlatformCommissionConfigSerializer},
        summary="Create or override commission policy (Admin only)",
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = PlatformCommissionConfigSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cfg = serializer.save()
        return Response(PlatformCommissionConfigSerializer(cfg).data, status=status.HTTP_201_CREATED)


class PriceEstimateView(APIView):
    """Estimate price breakdown for a service window without persisting a booking."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=PriceEstimateRequestSerializer,
        responses={200: PriceEstimateResponseSerializer},
        summary="Upfront price estimate breakdown",
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = PriceEstimateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        society = None
        if data.get("society_id"):
            society = get_object_or_404(Society, id=data["society_id"])

        estimate = PricingCalculatorService.estimate_price(
            society=society,
            duration_minutes=data["duration_minutes"],
            meal_type=data["meal_type"],
            pricing_type=data["pricing_type"],
        )
        return Response(estimate, status=status.HTTP_200_OK)


class BookingPriceBreakdownDetailView(APIView):
    """Retrieve immutable price breakdown snapshot for a booking."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={200: BookingPriceBreakdownSerializer},
        summary="Get booking price breakdown and financial snapshot",
    )
    def get(self, request: Request, booking_id: str, *args: Any, **kwargs: Any) -> Response:
        booking = get_object_or_404(Booking.objects.select_related("household"), id=booking_id)

        # Check authorization: Resident of household, assigned cook, or admin
        user = request.user
        is_admin = user.is_superuser or user.has_role(Role.PLATFORM_ADMIN) or user.has_role(Role.SOCIETY_ADMIN)
        is_household_member = booking.household.members.filter(user=user, is_active=True).exists()
        is_assigned_cook = booking.assignments.filter(cook__user=user).exists()

        if not (is_admin or is_household_member or is_assigned_cook):
            raise PermissionDenied("You are not authorized to view this booking price breakdown.")

        # If breakdown does not exist yet (e.g. legacy booking), compute and persist now
        if not hasattr(booking, "price_breakdown"):
            breakdown = PricingCalculatorService.calculate_price_breakdown(booking, persist=True)
        else:
            breakdown = booking.price_breakdown

        return Response(BookingPriceBreakdownSerializer(breakdown).data, status=status.HTTP_200_OK)


# ==============================================================================
# Phase 10 Views: Online Payments, Cash Collections, Commission & Payouts
# ==============================================================================

class PaymentOrderCreateView(APIView):
    """Initiate an online payment order for a booking or subscription."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=PaymentOrderCreateRequestSerializer,
        responses={201: PaymentOrderSerializer},
        summary="Create online payment order",
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = PaymentOrderCreateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        booking = None
        subscription = None
        household = None

        if data.get("booking_id"):
            booking = get_object_or_404(Booking.objects.select_related("household"), id=data["booking_id"])
            household = booking.household
        elif data.get("subscription_id"):
            subscription = get_object_or_404(
                HouseholdPackageSubscription.objects.select_related("household"),
                id=data["subscription_id"],
            )
            household = subscription.household

        if not household:
            raise PermissionDenied("Either booking_id or subscription_id must be provided.")

        # Check membership
        is_member = household.members.filter(user=request.user, is_active=True).exists()
        is_admin = request.user.is_superuser or request.user.has_role(Role.PLATFORM_ADMIN)
        if not (is_member or is_admin):
            raise PermissionDenied("You are not authorized to make payments for this household.")

        order = PaymentService.create_payment_order(
            household=household,
            booking=booking,
            subscription=subscription,
            idempotency_key=data.get("idempotency_key", ""),
        )
        return Response(PaymentOrderSerializer(order).data, status=status.HTTP_201_CREATED)


class PaymentVerifyView(APIView):
    """Verify online payment signature returned by the client gateway."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=PaymentVerifyRequestSerializer,
        responses={200: PaymentTransactionSerializer},
        summary="Verify payment signature and finalize order",
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = PaymentVerifyRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            txn = PaymentService.verify_and_confirm_payment(
                order_id=data["provider_order_id"],
                provider_payment_id=data["provider_payment_id"],
                signature=data["signature"],
                payment_method=data.get("payment_method", "card"),
            )
            return Response(PaymentTransactionSerializer(txn).data, status=status.HTTP_200_OK)
        except Exception as exc:
            msg = exc.messages[0] if hasattr(exc, "messages") else str(exc)
            return Response(
                {"detail": msg, "code": "PAYMENT_VERIFICATION_FAILED"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class PaymentWebhookView(APIView):
    """Public webhook receiver with signature validation."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=None,
        responses={200: dict},
        summary="Payment gateway webhook listener",
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        signature_header = (
            request.headers.get("X-Razorpay-Signature")
            or request.headers.get("X-Signature")
            or request.headers.get("X-Mock-Signature")
            or ""
        )
        result = PaymentService.process_webhook_event(
            payload_bytes=request.body,
            signature_header=signature_header,
        )
        return Response(result, status=status.HTTP_200_OK)


class PaymentRefundView(APIView):
    """Issue refund against a successful payment transaction (Admin only)."""

    permission_classes = [permissions.IsAuthenticated, (IsPlatformAdmin | IsSocietyAdmin)]

    @extend_schema(
        request=RefundRequestSerializer,
        responses={201: RefundRecordSerializer},
        summary="Issue payment refund (Admin only)",
    )
    def post(self, request: Request, transaction_id: str, *args: Any, **kwargs: Any) -> Response:
        serializer = RefundRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        refund = PaymentService.issue_refund(
            transaction_id=transaction_id,
            amount_minor_units=data.get("amount_minor_units"),
            reason=data.get("reason", ""),
        )
        return Response(RefundRecordSerializer(refund).data, status=status.HTTP_201_CREATED)


class PaymentHistoryView(APIView):
    """List transaction history for current user's households or cooks."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        responses={200: PaymentTransactionSerializer(many=True)},
        summary="List payment transaction history",
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = request.user
        if user.is_superuser or user.has_role(Role.PLATFORM_ADMIN):
            txns = PaymentTransaction.objects.all().select_related("payment_order")
        else:
            household_ids = user.household_memberships.filter(is_active=True).values_list("household_id", flat=True)
            txns = PaymentTransaction.objects.filter(payment_order__household_id__in=household_ids).select_related("payment_order")

        return Response(PaymentTransactionSerializer(txns, many=True).data, status=status.HTTP_200_OK)


class CookCashReportView(APIView):
    """Cook reports cash collected physically from household for a visit."""

    permission_classes = [permissions.IsAuthenticated, IsCook]

    @extend_schema(
        request=CashReportRequestSerializer,
        responses={201: CashCollectionRecordSerializer},
        summary="Cook reports physical cash collection",
    )
    def post(self, request: Request, booking_id: str, *args: Any, **kwargs: Any) -> Response:
        booking = get_object_or_404(Booking.objects.select_related("household"), id=booking_id)
        cook = request.user.cook_profile

        # Verify cook was assigned to this booking
        if not booking.assignments.filter(cook=cook).exists():
            raise PermissionDenied("You were not assigned to this booking.")

        serializer = CashReportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        record = CashService.report_cash_collection(
            booking=booking,
            cook=cook,
            reported_amount_minor_units=data["reported_amount_minor_units"],
            cook_notes=data.get("cook_notes", ""),
        )
        return Response(CashCollectionRecordSerializer(record).data, status=status.HTTP_201_CREATED)


class HouseholdCashConfirmView(APIView):
    """Household confirms physical cash payment to cook."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=None,
        responses={200: CashCollectionRecordSerializer},
        summary="Household confirms cash paid to cook",
    )
    def post(self, request: Request, booking_id: str, *args: Any, **kwargs: Any) -> Response:
        booking = get_object_or_404(Booking.objects.select_related("household"), id=booking_id)
        is_member = booking.household.members.filter(user=request.user, is_active=True).exists()
        if not (is_member or request.user.is_superuser):
            raise PermissionDenied("Forbidden: Cannot confirm cash for this household.")

        record = CashService.confirm_cash_collection(booking=booking, household_user=request.user)
        return Response(CashCollectionRecordSerializer(record).data, status=status.HTTP_200_OK)


class HouseholdCashDisputeView(APIView):
    """Household disputes physical cash collection reported by cook."""

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=CashDisputeRequestSerializer,
        responses={200: CashCollectionRecordSerializer},
        summary="Household disputes physical cash collection",
    )
    def post(self, request: Request, booking_id: str, *args: Any, **kwargs: Any) -> Response:
        booking = get_object_or_404(Booking.objects.select_related("household"), id=booking_id)
        is_member = booking.household.members.filter(user=request.user, is_active=True).exists()
        if not (is_member or request.user.is_superuser):
            raise PermissionDenied("Forbidden: Cannot dispute cash for this household.")

        serializer = CashDisputeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        record = CashService.dispute_cash_collection(
            booking=booking,
            household_user=request.user,
            reason=serializer.validated_data["dispute_reason"],
        )
        return Response(CashCollectionRecordSerializer(record).data, status=status.HTTP_200_OK)


class AdminCashResolveView(APIView):
    """Admin arbitrates and resolves disputed cash collection."""

    permission_classes = [permissions.IsAuthenticated, (IsPlatformAdmin | IsSocietyAdmin)]

    @extend_schema(
        request=CashResolveRequestSerializer,
        responses={200: CashCollectionRecordSerializer},
        summary="Admin resolves cash dispute (Admin only)",
    )
    def post(self, request: Request, cash_record_id: str, *args: Any, **kwargs: Any) -> Response:
        serializer = CashResolveRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        record = CashService.admin_resolve_dispute(
            cash_record_id=cash_record_id,
            resolved_amount_minor_units=data["resolved_amount_minor_units"],
            admin_user=request.user,
            resolution_notes=data["resolution_notes"],
        )
        return Response(CashCollectionRecordSerializer(record).data, status=status.HTTP_200_OK)


class CookEarningsSummaryView(APIView):
    """Cook retrieves gross earnings, cash collections, and payable net balance."""

    permission_classes = [permissions.IsAuthenticated, IsCook]

    @extend_schema(
        responses={200: CookFinancialSummarySerializer},
        summary="Cook financial summary and net payable balance",
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        cook = request.user.cook_profile
        summary = PayoutService.get_cook_financial_summary(cook)
        return Response(CookFinancialSummarySerializer(summary).data, status=status.HTTP_200_OK)


class AdminCommissionLedgerListView(APIView):
    """Admin views platform commission ledger across cooks."""

    permission_classes = [permissions.IsAuthenticated, (IsPlatformAdmin | IsSocietyAdmin)]

    @extend_schema(
        responses={200: CommissionLedgerSerializer(many=True)},
        summary="List platform commission ledger entries (Admin only)",
    )
    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        qs = CommissionLedger.objects.all().select_related("cook__user", "booking")
        cook_id = request.query_params.get("cook_id")
        if cook_id:
            qs = qs.filter(cook_id=cook_id)
        return Response(CommissionLedgerSerializer(qs, many=True).data, status=status.HTTP_200_OK)


class AdminCookPayoutCreateView(APIView):
    """Admin processes payout disbursement for a cook."""

    permission_classes = [permissions.IsAuthenticated, (IsPlatformAdmin | IsSocietyAdmin)]

    @extend_schema(
        request=CookPayoutCreateRequestSerializer,
        responses={201: CookPayoutRecordSerializer},
        summary="Disburse cook payout batch (Admin only)",
    )
    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = CookPayoutCreateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        cook = get_object_or_404(CookProfile, id=data["cook_id"])
        payout = PayoutService.process_cook_payout(
            cook=cook,
            period_start=data["period_start"],
            period_end=data["period_end"],
            actor=request.user,
        )
        return Response(CookPayoutRecordSerializer(payout).data, status=status.HTTP_201_CREATED)

