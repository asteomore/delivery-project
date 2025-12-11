from django.db import models

class PackageType(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Package(models.Model):
    session_key = models.CharField(max_length=150, db_index=True)
    name = models.CharField(max_length=150)
    package_type = models.ForeignKey(PackageType, on_delete=models.CASCADE, related_name='packages')
    weight_kg = models.DecimalField(max_digits=10, decimal_places=3)
    content_price_usd = models.DecimalField(max_digits=12, decimal_places=2)
    delivery_price_rub = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.session_key})"