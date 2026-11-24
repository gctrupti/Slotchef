"""Serializers for Community domain (Society, Building, Apartment)."""

from __future__ import annotations

from rest_framework import serializers

from apps.communities.models import Apartment, Building, Society


class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = ["id", "society", "name", "code", "created_at"]
        read_only_fields = ["id", "created_at"]


class ApartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Apartment
        fields = ["id", "building", "unit_number", "floor", "created_at"]
        read_only_fields = ["id", "created_at"]


class SocietySerializer(serializers.ModelSerializer):
    buildings = BuildingSerializer(many=True, read_only=True)

    class Meta:
        model = Society
        fields = [
            "id",
            "name",
            "address",
            "timezone",
            "status",
            "buildings",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "buildings", "created_at", "updated_at"]

