from django.urls import path

from .views import (
    PackageAssignCompanyAPIView,
    PackageDetailAPIView,
    PackageListCreateAPIView,
    PackageTypeListAPIView,
    RecalculateDeliveryDebugAPIView,
)

urlpatterns = [
    path("package-types/", PackageTypeListAPIView.as_view(), name="package_types_list"),
    path("packages/", PackageListCreateAPIView.as_view(), name="packages_list_create"),
    path("packages/<int:pk>/", PackageDetailAPIView.as_view(), name="package_detail"),
    path(
        "packages/<int:pk>/assign-company/",
        PackageAssignCompanyAPIView.as_view(),
        name="package_assign_company",
    ),
    path(
        "debug/recalculate-delivery/",
        RecalculateDeliveryDebugAPIView.as_view(),
        name="recalculate_delivery_debug",
    ),
]
