from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveAPIView

from .models import Package, PackageType
from .serializers import (
    PackageCreateSerializer,
    PackageDetailSerializer,
    PackageListSerializer,
    PackageTypeSerializer,
)
from .utils import api_response


class PackageTypeListAPIView(ListAPIView):
    queryset = PackageType.objects.all()
    serializer_class = PackageTypeSerializer

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return api_response(data=response.data)


class PackageListCreateAPIView(ListCreateAPIView):
    def get_serializer_class(self):
        if self.request.method == "POST":
            return PackageCreateSerializer
        return PackageListSerializer

    def _get_session_key(self):
        session = self.request.session
        if not session.session_key:
            session.save()
        return session.session_key

    def get_queryset(self):
        session_key = self._get_session_key()
        queryset = Package.objects.filter(session_key=session_key)

        package_type_id = self.request.query_params.get("package_type_id")
        if package_type_id:
            queryset = queryset.filter(package_type_id=package_type_id)

        has_delivery_price = self.request.query_params.get("has_delivery_price")
        if has_delivery_price == "true":
            queryset = queryset.filter(delivery_price_rub__isnull=False)
        elif has_delivery_price == "false":
            queryset = queryset.filter(delivery_price_rub__isnull=True)

        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return api_response(data=response.data)

    def perform_create(self, serializer):
        session_key = self._get_session_key()
        serializer.save(session_key=session_key)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return api_response(data=response.data, status_code=response.status_code)


class PackageDetailAPIView(RetrieveAPIView):
    serializer_class = PackageDetailSerializer

    def _get_session_key(self):
        session = self.request.session
        if not session.session_key:
            session.save()
        return session.session_key

    def get_queryset(self):
        session_key = self._get_session_key()
        return Package.objects.filter(session_key=session_key)

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return api_response(data=response.data)
