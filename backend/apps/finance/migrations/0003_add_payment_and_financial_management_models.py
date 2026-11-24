# Generated for Phase 10: Payment and Financial Management

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('households', '0001_initial'),
        ('cooks', '0001_initial'),
        ('bookings', '0002_add_package_models'),
        ('finance', '0002_add_pricing_and_commission_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentOrder',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('amount_minor_units', models.BigIntegerField()),
                ('currency', models.CharField(default='INR', max_length=3)),
                ('provider', models.CharField(default='mock', max_length=64)),
                ('provider_order_id', models.CharField(db_index=True, max_length=128, unique=True)),
                ('status', models.CharField(choices=[('created', 'Created'), ('paid', 'Paid'), ('failed', 'Failed'), ('expired', 'Expired')], db_index=True, default='created', max_length=32)),
                ('idempotency_key', models.CharField(blank=True, db_index=True, max_length=128)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('booking', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payment_orders', to='bookings.booking')),
                ('household', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='payment_orders', to='households.household')),
                ('subscription', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payment_orders', to='bookings.householdpackagesubscription')),
            ],
            options={
                'db_table': 'finance_payment_order',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PaymentTransaction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('provider_payment_id', models.CharField(db_index=True, max_length=128)),
                ('amount_minor_units', models.BigIntegerField()),
                ('status', models.CharField(choices=[('success', 'Success'), ('failed', 'Failed'), ('refunded', 'Refunded')], db_index=True, default='success', max_length=32)),
                ('payment_method', models.CharField(default='card', max_length=64)),
                ('signature', models.CharField(blank=True, default='', max_length=255)),
                ('error_code', models.CharField(blank=True, default='', max_length=64)),
                ('error_description', models.TextField(blank=True, default='')),
                ('raw_payload', models.JSONField(blank=True, default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('payment_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='finance.paymentorder')),
            ],
            options={
                'db_table': 'finance_payment_transaction',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='RefundRecord',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('amount_minor_units', models.BigIntegerField()),
                ('reason', models.TextField(blank=True, default='')),
                ('provider_refund_id', models.CharField(blank=True, default='', max_length=128)),
                ('status', models.CharField(choices=[('requested', 'Requested'), ('processed', 'Processed'), ('failed', 'Failed')], db_index=True, default='processed', max_length=32)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('payment_transaction', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='refunds', to='finance.paymenttransaction')),
            ],
            options={
                'db_table': 'finance_refund_record',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='CashCollectionRecord',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('reported_amount_minor_units', models.BigIntegerField()),
                ('collected_at', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('reported', 'Reported by Cook'), ('confirmed', 'Confirmed by Household'), ('disputed', 'Disputed by Household'), ('resolved', 'Resolved by Admin')], db_index=True, default='reported', max_length=32)),
                ('cook_notes', models.TextField(blank=True, default='')),
                ('household_dispute_reason', models.TextField(blank=True, default='')),
                ('admin_resolution_notes', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('booking', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='cash_collection', to='bookings.booking')),
                ('cook', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='cash_collections', to='cooks.cookprofile')),
                ('household', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='cash_collections', to='households.household')),
            ],
            options={
                'db_table': 'finance_cash_collection',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='CommissionLedger',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('entry_type', models.CharField(choices=[('commission_accrued', 'Commission Accrued (Cash Liability)'), ('commission_deducted', 'Commission Deducted (Online Offset)'), ('commission_settled', 'Commission Settled')], db_index=True, max_length=32)),
                ('amount_minor_units', models.BigIntegerField(help_text='Commission amount in minor units.')),
                ('running_balance_minor_units', models.BigIntegerField(default=0, help_text='Cumulative net commission owed by cook to the platform.')),
                ('description', models.CharField(blank=True, default='', max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('booking', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='commission_ledger_entries', to='bookings.booking')),
                ('cook', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='commission_ledger_entries', to='cooks.cookprofile')),
            ],
            options={
                'db_table': 'finance_commission_ledger',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='CookPayoutRecord',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('period_start', models.DateField()),
                ('period_end', models.DateField()),
                ('gross_online_earnings_minor_units', models.BigIntegerField(default=0)),
                ('commission_deductions_minor_units', models.BigIntegerField(default=0)),
                ('net_payout_amount_minor_units', models.BigIntegerField(default=0)),
                ('currency', models.CharField(default='INR', max_length=3)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processed', 'Processed'), ('failed', 'Failed')], db_index=True, default='pending', max_length=32)),
                ('reference_id', models.CharField(blank=True, default='', max_length=128)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('processed_at', models.DateTimeField(blank=True, null=True)),
                ('cook', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='payout_records', to='cooks.cookprofile')),
            ],
            options={
                'db_table': 'finance_cook_payout_record',
                'ordering': ['-created_at'],
            },
        ),
    ]

