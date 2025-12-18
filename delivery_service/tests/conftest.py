import pytest
from rest_framework.test import APIClient

from packages.models import PackageType


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def package_types(db):
    return [
        PackageType.objects.create(name="одежда"),
        PackageType.objects.create(name="электроника"),
        PackageType.objects.create(name="разное"),
    ]


@pytest.fixture
def clothing_type(package_types):
    return package_types[0]
