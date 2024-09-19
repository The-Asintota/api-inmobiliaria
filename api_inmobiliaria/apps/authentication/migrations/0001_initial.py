# Generated by Django 5.1.1 on 2024-09-14 19:39

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="JWT",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        db_column="id", primary_key=True, serialize=False
                    ),
                ),
                (
                    "jti",
                    models.CharField(
                        db_column="jti",
                        db_index=True,
                        max_length=255,
                        unique=True,
                    ),
                ),
                ("token", models.TextField(db_column="token")),
                ("expires_at", models.DateTimeField(db_column="expires_at")),
                (
                    "date_joined",
                    models.DateTimeField(
                        auto_now_add=True, db_column="date_joined"
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        db_column="user",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "JWT",
                "verbose_name_plural": "JWT's",
            },
        ),
        migrations.CreateModel(
            name="JWTBlacklist",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        db_column="id", primary_key=True, serialize=False
                    ),
                ),
                (
                    "date_joined",
                    models.DateTimeField(
                        auto_now_add=True, db_column="date_joined"
                    ),
                ),
                (
                    "token",
                    models.OneToOneField(
                        db_column="token",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="authentication.jwt",
                    ),
                ),
            ],
            options={
                "verbose_name": "JWT Blacklist",
                "verbose_name_plural": "JWT Blacklist",
            },
        ),
    ]