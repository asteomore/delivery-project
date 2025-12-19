from django.db import models


class PackageType(models.Model):
    """Справочник типов посылок (одежда, электроника, разное)."""

    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Package(models.Model):
    """Посылка, привязанная к сессии пользователя без явной авторизации."""

    session_key = models.CharField(max_length=150, db_index=True)
    session_package_id = models.PositiveIntegerField()
    name = models.CharField(max_length=150)
    package_type = models.ForeignKey(PackageType, on_delete=models.CASCADE, related_name="packages")
    weight_kg = models.DecimalField(max_digits=10, decimal_places=3)
    content_price_usd = models.DecimalField(max_digits=12, decimal_places=2)
    delivery_price_rub = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True, db_index=True
    )
    company_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["session_key", "session_package_id"],
                name="unique_session_package_id",
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.session_key})"
