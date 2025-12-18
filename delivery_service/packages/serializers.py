from rest_framework import serializers

from .models import Package, PackageType


class PackageTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackageType
        fields = ("id", "name")


class PackageCreateSerializer(serializers.ModelSerializer):
    package_type_id = serializers.PrimaryKeyRelatedField(
        source="package_type",
        queryset=PackageType.objects.all(),
    )

    class Meta:
        model = Package
        fields = (
            "id",
            "name",
            "weight_kg",
            "content_price_usd",
            "package_type_id",
            "session_package_id",
        )
        read_only_fields = ("id", "session_package_id")

    def validate_weight_kg(self, value):
        if value <= 0:
            raise serializers.ValidationError("Вес должен быть больше 0")
        return value

    def validate_content_price_usd(self, value):
        if value <= 0:
            raise serializers.ValidationError("Цена должна быть больше 0")
        return value


class PackageDetailSerializer(serializers.ModelSerializer):
    package_type = PackageTypeSerializer(read_only=True)
    delivery_price_rub = serializers.SerializerMethodField()

    class Meta:
        model = Package
        fields = (
            "session_package_id",
            "id",
            "name",
            "weight_kg",
            "content_price_usd",
            "delivery_price_rub",
            "package_type",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "session_package_id",
            "id",
            "delivery_price_rub",
            "package_type",
            "created_at",
            "updated_at",
        )

    def get_delivery_price_rub(self, obj):
        if obj.delivery_price_rub is None:
            return "Не рассчитано"
        return str(obj.delivery_price_rub)


class PackageListSerializer(serializers.ModelSerializer):
    package_type = PackageTypeSerializer(read_only=True)
    delivery_price_rub = serializers.SerializerMethodField()

    class Meta:
        model = Package
        fields = (
            "session_package_id",
            "id",
            "name",
            "weight_kg",
            "content_price_usd",
            "delivery_price_rub",
            "package_type",
        )
        read_only_fields = (
            "session_package_id",
            "id",
            "delivery_price_rub",
            "package_type",
        )

    def get_delivery_price_rub(self, obj):
        if obj.delivery_price_rub is None:
            return "Не рассчитано"
        return str(obj.delivery_price_rub)
