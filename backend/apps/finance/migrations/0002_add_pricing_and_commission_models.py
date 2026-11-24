# Generated for Phase 8: Payment Foundation and Pricing

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('communities', '0001_initial'),
        ('bookings', '0001_initial'),
        ('finance', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ServicePricingRule',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=128)),
                ('code', models.CharField(db_index=True, max_length=64)),
                ('pricing_type', models.CharField(choices=[('per_visit', 'Per-Visit Pricing'), ('weekly_plan', 'Weekly Subscription Base'), ('monthly_plan', 'Monthly Subscription Base')], default='per_visit', max_length=32)),
                ('base_fee_minor_units', models.BigIntegerField(default=20000, help_text='Fixed base visit fee in minor currency units (e.g., 20000 paise = 200 INR).')),
                ('per_minute_rate_minor_units', models.BigIntegerField(default=250, help_text='Rate per service minute in minor units (e.g., 250 paise = 2.5 INR/min).')),
                ('breakfast_multiplier', models.DecimalField(decimal_places=2, default=1.0, max_digits=4)),
                ('lunch_multiplier', models.DecimalField(decimal_places=2, default=1.2, max_digits=4)),
                ('dinner_multiplier', models.DecimalField(decimal_places=2, default=1.25, max_digits=4)),
                ('snacks_multiplier', models.DecimalField(decimal_places=2, default=0.9, max_digits=4)),
                ('currency', models.CharField(default='INR', max_length=3)),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('effective_from', models.DateField(blank=True, null=True)),
                ('effective_to', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('society', models.ForeignKey(blank=True, help_text='Society-specific override; null indicates global platform baseline.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pricing_rules', to='communities.society')),
            ],
            options={
                'db_table': 'finance_service_pricing_rule',
                'ordering': ['-is_active', 'society', 'name'],
            },
        ),
        migrations.CreateModel(
            name='PlatformCommissionConfig',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('commission_type', models.CharField(choices=[('percentage', 'Percentage of Subtotal'), ('fixed', 'Fixed Fee Per Visit'), ('hybrid', 'Hybrid (Percentage + Fixed Fee)')], default='percentage', max_length=32)),
                ('percentage_rate', models.DecimalField(decimal_places=2, default=15.0, help_text='Platform commission percentage (e.g. 15.00%).', max_digits=5)),
                ('fixed_fee_minor_units', models.BigIntegerField(default=0, help_text='Fixed commission fee per visit in minor units (paise).')),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('society', models.ForeignKey(blank=True, help_text='Society-specific commission override; null indicates global default.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='commission_configs', to='communities.society')),
            ],
            options={
                'db_table': 'finance_commission_config',
                'ordering': ['-is_active', 'society'],
            },
        ),
        migrations.CreateModel(
            name='BookingPriceBreakdown',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('base_fee_minor_units', models.BigIntegerField()),
                ('duration_fee_minor_units', models.BigIntegerField()),
                ('meal_multiplier', models.DecimalField(decimal_places=2, default=1.0, max_digits=4)),
                ('subtotal_minor_units', models.BigIntegerField()),
                ('platform_commission_minor_units', models.BigIntegerField()),
                ('cook_earnings_minor_units', models.BigIntegerField()),
                ('tax_minor_units', models.BigIntegerField(default=0)),
                ('discount_minor_units', models.BigIntegerField(default=0)),
                ('total_amount_minor_units', models.BigIntegerField()),
                ('currency', models.CharField(default='INR', max_length=3)),
                ('snapshot_metadata', models.JSONField(blank=True, default=dict, help_text='Immutable audit snapshot of multipliers and formula inputs at calculation time.')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('booking', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='price_breakdown', to='bookings.booking')),
                ('commission_config', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='applied_breakdowns', to='finance.platformcommissionconfig')),
                ('pricing_rule', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='applied_breakdowns', to='finance.servicepricingrule')),
            ],
            options={
                'db_table': 'finance_booking_price_breakdown',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='servicepricingrule',
            index=models.Index(fields=['code', 'is_active'], name='idx_pricing_code_active'),
        ),
    ]

