"""Adjust AuthAuditLog action choices."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("assets_auth", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="authauditlog",
            name="action",
            field=models.CharField(
                choices=[
                    ("login", "Login"),
                    ("register", "Register"),
                    ("logout", "Logout"),
                    ("refresh", "Refresh"),
                    ("access_denied", "Access Denied"),
                    ("token_revoked", "Token Revoked"),
                ],
                max_length=32,
            ),
        ),
    ]
