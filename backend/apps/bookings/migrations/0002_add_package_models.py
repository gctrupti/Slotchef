# Generated for Phase 9: Package Management

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('communities', '0001_initial'),
        ('cooks', '0001_initial'),
        ('households', '0001_initial'),
        ('bookings', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PackagePlan',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=128)),
                ('code', models.CharField(db_index=True, max_length=64, unique=True)),
                ('plan_type', models.CharField(choices=[('weekly', 'Weekly Package'), ('monthly', 'Monthly Package'), ('custom', 'Custom Frequency Package')], default='weekly', max_length=32)),
                ('visit_frequency_per_week', models.PositiveIntegerField(default=5, help_text='Nominal visits per week (e.g. 5 days / week).')),
                ('total_visits', models.PositiveIntegerField(default=5, help_text='Total number of visits entitled within this package cycle.')),
                ('validity_days', models.PositiveIntegerField(default=7, help_text='Validity duration in calendar days (e.g. 7 for weekly, 30 for monthly).')),
                ('price_minor_units', models.BigIntegerField(default=95000, help_text='Package price in minor currency units (e.g. 95000 paise = 950 INR).')),
                ('currency', models.CharField(default='INR', max_length=3)),
                ('meal_type', models.CharField(choices=[('breakfast', 'Breakfast'), ('lunch', 'Lunch'), ('dinner', 'Dinner'), ('snacks', 'Snacks')], default='breakfast', max_length=32)),
                ('default_duration_minutes', models.PositiveIntegerField(default=45)),
                ('max_pause_days', models.PositiveIntegerField(default=7, help_text='Maximum total days this package can be paused.')),
                ('is_active', models.BooleanField(db_index=True, default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('society', models.ForeignKey(blank=True, help_text='Society-specific package; null indicates global platform plan.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='package_plans', to='communities.society')),
            ],
            options={
                'db_table': 'booking_package_plan',
                'ordering': ['-is_active', 'plan_type', 'price_minor_units'],
            },
        ),
        migrations.CreateModel(
            name='HouseholdPackageSubscription',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('active', 'Active'), ('paused', 'Paused'), ('completed', 'Completed'), ('cancelled', 'Cancelled'), ('expired', 'Expired')], db_index=True, default='active', max_length=32)),
                ('total_entitled_visits', models.PositiveIntegerField()),
                ('used_visits', models.PositiveIntegerField(default=0)),
                ('missed_visits', models.PositiveIntegerField(default=0)),
                ('cancelled_visits', models.PositiveIntegerField(default=0)),
                ('preferred_weekdays', models.JSONField(default=list, help_text='List of weekday integers (0=Monday, 6=Sunday) for recurring visits.')),
                ('preferred_start_minute', models.PositiveIntegerField(default=450)),
                ('preferred_end_minute', models.PositiveIntegerField(default=540)),
                ('start_date', models.DateField(db_index=True)),
                ('end_date', models.DateField(db_index=True)),
                ('paused_at', models.DateTimeField(blank=True, null=True)),
                ('pause_resumes_at', models.DateField(blank=True, null=True)),
                ('auto_renew', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('household', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='package_subscriptions', to='households.household')),
                ('package_plan', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='subscriptions', to='bookings.packageplan')),
                ('preferred_cook', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='preferred_subscriptions', to='cooks.cookprofile')),
            ],
            options={
                'db_table': 'booking_household_package_subscription',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PackageBookingLink',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_missed', models.BooleanField(default=False)),
                ('is_rescheduled', models.BooleanField(default=False)),
                ('original_service_date', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('booking', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='package_link', to='bookings.booking')),
                ('subscription', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='booking_links', to='bookings.householdpackagesubscription')),
            ],
            options={
                'db_table': 'booking_package_booking_link',
                'ordering': ['booking__service_date'],
            },
        ),
        migrations.AddIndex(
            model_name='householdpackagesubscription',
            index=models.Index(fields=['household', 'status'], name='idx_sub_hh_status'),
        ),
    ]

