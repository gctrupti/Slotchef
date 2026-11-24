"""Core system views (health check)."""

from __future__ import annotations

import logging

from django.db import DatabaseError, connection
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    """Verify application and PostgreSQL database readiness."""

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        summary="Backend health check",
        responses={
            200: OpenApiResponse(description="Backend and PostgreSQL database are healthy."),
            503: OpenApiResponse(description="PostgreSQL database is unreachable."),
        },
        tags=["system"],
    )
    def get(self, request: Request) -> Response:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
                cursor.fetchone()
        except DatabaseError:
            logger.exception("Database health check failed.")
            return Response(
                {
                    "status": "degraded",
                    "service": "slotchef-backend",
                    "database": "unavailable",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "status": "ok",
                "service": "slotchef-backend",
                "database": "ok",
            },
            status=status.HTTP_200_OK,
        )

