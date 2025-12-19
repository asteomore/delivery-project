import logging

from django.conf import settings
from django.db import transaction
from django.db.models import Max
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import serializers, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveAPIView
from rest_framework.views import APIView

from .models import Package, PackageType
from .serializers import (
    PackageAssignCompanySerializer,
    PackageCreateSerializer,
    PackageDetailSerializer,
    PackageListSerializer,
    PackageTypeSerializer,
)
from .tasks import update_packages_delivery_price
from .utils import api_response, get_session_key

logger = logging.getLogger("packages")


@extend_schema(
    responses=OpenApiResponse(
        response=PackageTypeSerializer,
        description="Список типов посылок в обёртке {status, data, error}",
    )
)
class PackageTypeListAPIView(ListAPIView):
    """Список доступных типов посылок."""

    queryset = PackageType.objects.all()
    serializer_class = PackageTypeSerializer

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return api_response(data=response.data)


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="package_type_id",
            type=int,
            description="Фильтр по ID типа посылки",
            required=False,
        ),
        OpenApiParameter(
            name="has_delivery_price",
            type=str,
            description="Наличие рассчитанной стоимости (yes/no/true/false/1/0)",
            required=False,
        ),
    ],
    responses=OpenApiResponse(
        response=PackageListSerializer,
        description="Список посылок в обёртке {status, data, error}",
    ),
)
class PackageListCreateAPIView(ListCreateAPIView):
    """Создание посылок и получение списка посылок текущей сессии с фильтрами и пагинацией."""

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PackageCreateSerializer
        return PackageListSerializer

    def get_queryset(self):
        session_key = get_session_key(self.request)
        queryset = Package.objects.filter(session_key=session_key)

        package_type_id = self.request.query_params.get("package_type_id")
        if package_type_id:
            queryset = queryset.filter(package_type_id=package_type_id)

        has_delivery_price = self.request.query_params.get("has_delivery_price")
        if has_delivery_price is not None:
            value = has_delivery_price.lower()
            if value in ("yes", "true", "1"):
                queryset = queryset.filter(delivery_price_rub__isnull=False)
            elif value in ("no", "false", "0"):
                queryset = queryset.filter(delivery_price_rub__isnull=True)

        return queryset

    def list(self, request, *args, **kwargs):
        logger.info(
            "Запрос списка посылок",
            extra={
                "session_key": get_session_key(request),
                "package_type_id": request.query_params.get("package_type_id"),
                "has_delivery_price": request.query_params.get("has_delivery_price"),
            },
        )
        response = super().list(request, *args, **kwargs)
        return api_response(data=response.data)

    def perform_create(self, serializer):
        session_key = get_session_key(self.request)
        with transaction.atomic():
            last_id = (
                Package.objects.filter(session_key=session_key)
                .aggregate(max_id=Max("session_package_id"))
                .get("max_id")
                or 0
            )
            session_package_id = last_id + 1
            serializer.save(session_key=session_key, session_package_id=session_package_id)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        logger.info(
            "Создана посылка",
            extra={
                "session_key": get_session_key(request),
                "package_id": response.data.get("id"),
                "session_package_id": response.data.get("session_package_id"),
            },
        )
        return api_response(data=response.data, status_code=response.status_code)


@extend_schema(
    responses=OpenApiResponse(
        response=PackageDetailSerializer,
        description="Детали посылки в обёртке {status, data, error}",
    )
)
class PackageDetailAPIView(RetrieveAPIView):
    """Детальная информация о посылке в рамках текущей сессии."""

    serializer_class = PackageDetailSerializer
    lookup_field = "pk"

    def get_queryset(self):
        session_key = get_session_key(self.request)
        return Package.objects.filter(session_key=session_key)

    def get_object(self):
        queryset = self.get_queryset()
        pk = self.kwargs.get("pk")
        try:
            obj = queryset.get(pk=pk)
        except Package.DoesNotExist:
            from rest_framework.exceptions import NotFound

            raise NotFound("Посылка не найдена или не принадлежит вашей сессии")

        return obj

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        logger.info(
            "Запрос деталей посылки",
            extra={
                "session_key": get_session_key(request),
                "package_pk": kwargs.get("pk"),
            },
        )
        return api_response(data=response.data)


@extend_schema(
    responses=OpenApiResponse(
        response=None,
        description="Привязка посылки к транспортной компании в обёртке {status, data, error}",
    )
)
class PackageAssignCompanyAPIView(APIView):
    """Привязать посылку к транспортной компании с гарантией единственного исполнителя."""

    def post(self, request, pk, *args, **kwargs):
        serializer = PackageAssignCompanySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company_id = serializer.validated_data["company_id"]

        session_key = get_session_key(request)

        with transaction.atomic():
            try:
                package = Package.objects.select_for_update().get(pk=pk, session_key=session_key)
            except Package.DoesNotExist:
                raise NotFound("Посылка не найдена или не принадлежит вашей сессии")

            if package.company_id is not None:
                return api_response(
                    success=False,
                    error_code="ALREADY_ASSIGNED",
                    message="Посылка уже привязана к транспортной компании",
                    status_code=status.HTTP_409_CONFLICT,
                )

            package.company_id = company_id
            package.save(update_fields=["company_id"])

        logger.info(
            "Посылка привязана к компании",
            extra={
                "session_key": session_key,
                "package_pk": package.pk,
                "company_id": company_id,
            },
        )

        return api_response(
            data={
                "session_package_id": package.session_package_id,
                "company_id": package.company_id,
            },
            status_code=status.HTTP_200_OK,
        )


class DebugTaskResponseSerializer(serializers.Serializer):
    task_id = serializers.CharField()


class RecalculateDeliveryDebugAPIView(APIView):
    """Отладочный эндпоинт для ручного пересчёта стоимости доставки при DEBUG=True."""

    def post(self, request, *args, **kwargs):
        if not settings.DEBUG:
            raise PermissionDenied("Этот эндпоинт доступен только в режиме DEBUG")

        logger.info("Перерасчет стоимости доставки!")
        task = update_packages_delivery_price.delay()
        return api_response(
            data={"task_id": task.id},
            status_code=status.HTTP_202_ACCEPTED,
        )
