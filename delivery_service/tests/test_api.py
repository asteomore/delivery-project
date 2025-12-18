from decimal import Decimal

import pytest
from django.test import override_settings

from packages.models import Package


@pytest.mark.django_db
class TestPackageTypesAPI:
    def test_list_package_types(self, api_client, package_types):
        response = api_client.get("/api/v1/package-types/")

        assert response.status_code == 200
        assert response.data["status"] is True
        assert response.data["data"]["count"] == 3


@pytest.mark.django_db
class TestPackagesAPI:
    def test_create_package_success(self, api_client, clothing_type):
        data = {
            "name": "Тестовая посылка",
            "weight_kg": "2.5",
            "content_price_usd": "100.00",
            "package_type_id": clothing_type.id,
        }
        response = api_client.post("/api/v1/packages/", data, format="json")

        assert response.status_code == 201
        assert response.data["status"] is True
        assert response.data["data"]["name"] == "Тестовая посылка"
        assert "session_package_id" in response.data["data"]

    def test_create_package_negative_weight(self, api_client, clothing_type):
        data = {
            "name": "Тест",
            "weight_kg": "-1",
            "content_price_usd": "100",
            "package_type_id": clothing_type.id,
        }
        response = api_client.post("/api/v1/packages/", data, format="json")

        assert response.status_code == 400
        assert response.data["status"] is False
        assert "error" in response.data

    def test_create_package_zero_weight(self, api_client, clothing_type):
        data = {
            "name": "Тест",
            "weight_kg": "0",
            "content_price_usd": "100",
            "package_type_id": clothing_type.id,
        }
        response = api_client.post("/api/v1/packages/", data, format="json")

        assert response.status_code == 400
        assert response.data["status"] is False
        assert "error" in response.data

    def test_create_package_negative_price(self, api_client, clothing_type):
        data = {
            "name": "Тест",
            "weight_kg": "1",
            "content_price_usd": "-50",
            "package_type_id": clothing_type.id,
        }
        response = api_client.post("/api/v1/packages/", data, format="json")

        assert response.status_code == 400
        assert response.data["status"] is False

    def test_create_package_zero_price(self, api_client, clothing_type):
        data = {
            "name": "Тест",
            "weight_kg": "1",
            "content_price_usd": "0",
            "package_type_id": clothing_type.id,
        }
        response = api_client.post("/api/v1/packages/", data, format="json")

        assert response.status_code == 400
        assert response.data["status"] is False

    def test_list_user_packages(self, api_client, clothing_type):
        session = api_client.session
        session.save()

        Package.objects.create(
            session_key=session.session_key,
            session_package_id=1,
            name="Посылка 1",
            weight_kg=Decimal("1.5"),
            content_price_usd=Decimal("50.00"),
            package_type=clothing_type,
        )

        response = api_client.get("/api/v1/packages/")

        assert response.status_code == 200
        assert response.data["status"] is True

    def test_get_package_detail(self, api_client, clothing_type):
        session = api_client.session
        session.save()

        package = Package.objects.create(
            session_key=session.session_key,
            session_package_id=1,
            name="Посылка детали",
            weight_kg=Decimal("3.0"),
            content_price_usd=Decimal("200.00"),
            package_type=clothing_type,
        )

        response = api_client.get(f"/api/v1/packages/{package.id}/")

        assert response.status_code == 200
        assert response.data["status"] is True
        assert response.data["data"]["name"] == "Посылка детали"

    def test_delivery_price_not_calculated(self, api_client, clothing_type):
        session = api_client.session
        session.save()

        package = Package.objects.create(
            session_key=session.session_key,
            session_package_id=1,
            name="Без цены",
            weight_kg=Decimal("1.0"),
            content_price_usd=Decimal("50.00"),
            package_type=clothing_type,
            delivery_price_rub=None,
        )

        response = api_client.get(f"/api/v1/packages/{package.id}/")

        assert response.data["data"]["delivery_price_rub"] == "Не рассчитано"

    def test_filter_by_package_type(self, api_client, package_types):
        session = api_client.session
        session.save()

        Package.objects.create(
            session_key=session.session_key,
            session_package_id=1,
            name="Одежда",
            weight_kg=Decimal("1.0"),
            content_price_usd=Decimal("50.00"),
            package_type=package_types[0],
        )
        Package.objects.create(
            session_key=session.session_key,
            session_package_id=2,
            name="Электроника",
            weight_kg=Decimal("2.0"),
            content_price_usd=Decimal("100.00"),
            package_type=package_types[1],
        )

        response = api_client.get(f"/api/v1/packages/?package_type_id={package_types[0].id}")

        assert response.status_code == 200
        assert response.data["data"]["count"] == 1
        assert response.data["data"]["results"][0]["name"] == "Одежда"

    def test_filter_by_has_delivery_price_true(self, api_client, clothing_type):
        session = api_client.session
        session.save()

        Package.objects.create(
            session_key=session.session_key,
            session_package_id=1,
            name="С ценой",
            weight_kg=Decimal("1.0"),
            content_price_usd=Decimal("50.00"),
            package_type=clothing_type,
            delivery_price_rub=Decimal("500.00"),
        )
        Package.objects.create(
            session_key=session.session_key,
            session_package_id=2,
            name="Без цены",
            weight_kg=Decimal("2.0"),
            content_price_usd=Decimal("100.00"),
            package_type=clothing_type,
            delivery_price_rub=None,
        )

        response = api_client.get("/api/v1/packages/?has_delivery_price=true")

        assert response.status_code == 200
        assert response.data["data"]["count"] == 1
        assert response.data["data"]["results"][0]["name"] == "С ценой"

    def test_filter_by_has_delivery_price_false(self, api_client, clothing_type):
        session = api_client.session
        session.save()

        Package.objects.create(
            session_key=session.session_key,
            session_package_id=1,
            name="С ценой",
            weight_kg=Decimal("1.0"),
            content_price_usd=Decimal("50.00"),
            package_type=clothing_type,
            delivery_price_rub=Decimal("500.00"),
        )
        Package.objects.create(
            session_key=session.session_key,
            session_package_id=2,
            name="Без цены",
            weight_kg=Decimal("2.0"),
            content_price_usd=Decimal("100.00"),
            package_type=clothing_type,
            delivery_price_rub=None,
        )

        response = api_client.get("/api/v1/packages/?has_delivery_price=no")

        assert response.status_code == 200
        assert response.data["data"]["count"] == 1
        assert response.data["data"]["results"][0]["name"] == "Без цены"

    def test_session_package_id_increment(self, api_client, clothing_type):
        data1 = {
            "name": "Посылка 1",
            "weight_kg": "1.0",
            "content_price_usd": "50.00",
            "package_type_id": clothing_type.id,
        }
        response1 = api_client.post("/api/v1/packages/", data1, format="json")

        data2 = {
            "name": "Посылка 2",
            "weight_kg": "2.0",
            "content_price_usd": "100.00",
            "package_type_id": clothing_type.id,
        }
        response2 = api_client.post("/api/v1/packages/", data2, format="json")

        data3 = {
            "name": "Посылка 3",
            "weight_kg": "3.0",
            "content_price_usd": "150.00",
            "package_type_id": clothing_type.id,
        }
        response3 = api_client.post("/api/v1/packages/", data3, format="json")

        assert response1.data["data"]["session_package_id"] == 1
        assert response2.data["data"]["session_package_id"] == 2
        assert response3.data["data"]["session_package_id"] == 3

    def test_pagination(self, api_client, clothing_type):
        session = api_client.session
        session.save()

        # Создаём 15 посылок (больше чем PAGE_SIZE=10)
        for i in range(1, 16):
            Package.objects.create(
                session_key=session.session_key,
                session_package_id=i,
                name=f"Посылка {i}",
                weight_kg=Decimal("1.0"),
                content_price_usd=Decimal("50.00"),
                package_type=clothing_type,
            )

        response_page1 = api_client.get("/api/v1/packages/")
        assert response_page1.status_code == 200
        assert response_page1.data["data"]["count"] == 15
        assert len(response_page1.data["data"]["results"]) == 10

        response_page2 = api_client.get("/api/v1/packages/?page=2")
        assert response_page2.status_code == 200
        assert len(response_page2.data["data"]["results"]) == 5

    def test_session_isolation(self, api_client, clothing_type):
        session1 = api_client.session
        session1.save()
        session1_key = session1.session_key

        Package.objects.create(
            session_key=session1_key,
            session_package_id=1,
            name="Посылка сессии 1",
            weight_kg=Decimal("1.0"),
            content_price_usd=Decimal("50.00"),
            package_type=clothing_type,
        )

        from rest_framework.test import APIClient

        api_client2 = APIClient()
        session2 = api_client2.session
        session2.save()
        session2_key = session2.session_key

        Package.objects.create(
            session_key=session2_key,
            session_package_id=1,
            name="Посылка сессии 2",
            weight_kg=Decimal("2.0"),
            content_price_usd=Decimal("100.00"),
            package_type=clothing_type,
        )

        response1 = api_client.get("/api/v1/packages/")
        assert response1.data["data"]["count"] == 1
        assert response1.data["data"]["results"][0]["name"] == "Посылка сессии 1"

        response2 = api_client2.get("/api/v1/packages/")
        assert response2.data["data"]["count"] == 1
        assert response2.data["data"]["results"][0]["name"] == "Посылка сессии 2"


@pytest.mark.django_db
class TestDebugAPI:
    def test_recalculate_delivery_debug(self, api_client):
        with override_settings(DEBUG=True):
            response = api_client.post("/api/v1/debug/recalculate-delivery/")
        assert response.status_code == 202
        assert response.data["status"] is True
        assert "task_id" in response.data["data"]
        assert response.data["data"]["task_id"] is not None

    def test_assign_company_only_once(self, api_client, clothing_type):
        session = api_client.session
        session.save()

        package = Package.objects.create(
            session_key=session.session_key,
            session_package_id=1,
            name="Для компании",
            weight_kg=Decimal("1.0"),
            content_price_usd=Decimal("50.00"),
            package_type=clothing_type,
        )

        resp1 = api_client.post(
            f"/api/v1/packages/{package.id}/assign-company/",
            {"company_id": 123},
            format="json",
        )
        assert resp1.status_code == 200
        assert resp1.data["data"]["company_id"] == 123

        resp2 = api_client.post(
            f"/api/v1/packages/{package.id}/assign-company/",
            {"company_id": 456},
            format="json",
        )
        assert resp2.status_code == 409
        assert resp2.data["status"] is False
        assert resp2.data["error"]["code"] == "ALREADY_ASSIGNED"
