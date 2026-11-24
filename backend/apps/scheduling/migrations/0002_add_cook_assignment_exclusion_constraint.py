"""Add PostgreSQL GiST exclusion constraint preventing overlapping active assignments per cook."""

from __future__ import annotations

from django.db import migrations


def apply_exclusion_constraint(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute("""
        CREATE EXTENSION IF NOT EXISTS btree_gist;
        ALTER TABLE "schedule_cook_assignment"
        ADD CONSTRAINT "exclude_overlapping_cook_assignments"
        EXCLUDE USING gist (
            cook_id WITH =,
            tstzrange(start_at, end_at, '[)') WITH &&
        )
        WHERE (status IN ('CONFIRMED', 'STARTED', 'COMPLETED'));
    """)


def reverse_exclusion_constraint(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute("""
        ALTER TABLE "schedule_cook_assignment"
        DROP CONSTRAINT IF EXISTS "exclude_overlapping_cook_assignments";
    """)


class Migration(migrations.Migration):
    dependencies = [
        ("scheduling", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(apply_exclusion_constraint, reverse_exclusion_constraint),
    ]
