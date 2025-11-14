from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Client",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("company_name", models.CharField(max_length=255)),
                ("contact_person", models.CharField(max_length=255)),
                ("email", models.EmailField(max_length=254)),
                ("phone", models.CharField(max_length=50)),
                (
                    "status",
                    models.CharField(
                        choices=[("active", "Active"), ("inactive", "Inactive")],
                        default="active",
                        max_length=20,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="SubscriptionPlan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("price_monthly", models.DecimalField(decimal_places=2, max_digits=10)),
                ("price_annual", models.DecimalField(decimal_places=2, max_digits=10)),
                ("is_active", models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name="Subscription",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "billing_cycle",
                    models.CharField(
                        choices=[("monthly", "Monthly"), ("annual", "Annual")], max_length=20
                    ),
                ),
                ("start_date", models.DateField()),
                ("end_date", models.DateField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("expired", "Expired"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="active",
                        max_length=20,
                    ),
                ),
                (
                    "client",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subscriptions",
                        to="core.client",
                    ),
                ),
                (
                    "plan",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="subscriptions",
                        to="core.subscriptionplan",
                    ),
                ),
            ],
            options={"ordering": ["-start_date"]},
        ),
        migrations.CreateModel(
            name="Invoice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("invoice_number", models.CharField(blank=True, max_length=20, unique=True)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("issue_date", models.DateField(default=django.utils.timezone.now)),
                ("due_date", models.DateField()),
                (
                    "status",
                    models.CharField(
                        choices=[("unpaid", "Unpaid"), ("paid", "Paid"), ("overdue", "Overdue")],
                        default="unpaid",
                        max_length=20,
                    ),
                ),
                ("last_reminder_sent_at", models.DateTimeField(blank=True, null=True)),
                (
                    "subscription",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="invoices",
                        to="core.subscription",
                    ),
                ),
            ],
            options={"ordering": ["-issue_date"]},
        ),
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("payment_date", models.DateField()),
                (
                    "payment_method",
                    models.CharField(
                        choices=[("bank_transfer", "Bank Transfer"), ("cheque", "Cheque")], max_length=20
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("received", "Received"), ("pending", "Pending")],
                        default="received",
                        max_length=20,
                    ),
                ),
                (
                    "subscription",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="payments",
                        to="core.subscription",
                    ),
                ),
            ],
            options={"ordering": ["-payment_date"]},
        ),
    ]
