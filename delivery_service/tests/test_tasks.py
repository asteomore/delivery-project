from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from packages.models import Package
from packages.tasks import update_packages_delivery_price, update_usd_rate


@pytest.mark.django_db
class TestCeleryTasks:
    @patch("packages.tasks.requests.get")
    @patch("packages.tasks.redis_client")
    def test_update_usd_rate_success(self, mock_redis, mock_requests):
        mock_response = Mock()
        mock_response.json.return_value = {"Valute": {"USD": {"Value": 95.50}}}
        mock_requests.return_value = mock_response

        result = update_usd_rate()

        assert result == 95.50
        mock_redis.set.assert_called_once()

    @patch("packages.tasks.redis_client")
    def test_update_packages_with_cached_rate(self, mock_redis, clothing_type):
        mock_redis.get.return_value = b"95.50"

        Package.objects.create(
            session_key="test_session",
            session_package_id=1,
            name="Тест",
            weight_kg=Decimal("2.0"),
            content_price_usd=Decimal("100.00"),
            package_type=clothing_type,
            delivery_price_rub=None,
        )

        update_packages_delivery_price()

        package = Package.objects.get(session_package_id=1)
        assert package.delivery_price_rub is not None
        assert package.delivery_price_rub > 0
