"""Views for Community domain."""

from __future__ import annotations

from rest_framework import generics, permissions

from apps.communities.models import Society
from apps.communities.serializers import SocietySerializer
from apps.identity.permissions import IsSocietyAdmin


class SocietyListCreateView(generics.ListCreateAPIView):
    """List all active societies or create a new society (admin only)."""

    queryset = Society.objects.prefetch_related("buildings").all()
    serializer_class = SocietySerializer

    def get_permissions(self) -> list[permissions.BasePermission]:
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), IsSocietyAdmin()]
        return [permissions.AllowAny()]


class SocietyDetailView(generics.RetrieveAPIView):
    """Retrieve details of a specific society."""

    queryset = Society.objects.prefetch_related("buildings").all()
    serializer_class = SocietySerializer
    permission_classes = [permissions.AllowAny]
