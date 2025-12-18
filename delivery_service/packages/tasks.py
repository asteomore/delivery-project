import decimal
import logging

import redis
import requests
from celery import shared_task
from django.conf import settings
from django.db import transaction

from .models import Package

logger = logging.getLogger("packages")
redis_client = redis.from_url(settings.CELERY_BROKER_URL)
USD_RATE_KEY = "usd_rub_rate"


@shared_task
def update_usd_rate():
    try:
        resp = requests.get("https://www.cbr-xml-daily.ru/daily_json.js", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        usd_rate = data["Valute"]["USD"]["Value"]
        redis_client.set(USD_RATE_KEY, usd_rate, ex=60 * 10)
        logger.info("Курс USD/RUB обновлён: %s", usd_rate)
        return usd_rate
    except (requests.RequestException, ValueError, KeyError):
        logger.exception("Не удалось обновить курс USD/RUB")
        return None


@shared_task
def update_packages_delivery_price():
    rate_bytes = redis_client.get(USD_RATE_KEY)

    if rate_bytes is None:
        raw_rate = update_usd_rate()
        if raw_rate is None:
            logger.warning("Пропускаю перерасчёт: нет курса USD/RUB")
            return
        usd_rate = decimal.Decimal(str(raw_rate))

    else:
        usd_rate = decimal.Decimal(rate_bytes.decode())
    logger.info("Запуск перерасчёта стоимости доставки, курс USD/RUB: %s", usd_rate)
    with transaction.atomic():
        packages = Package.objects.select_for_update(skip_locked=True).filter(
            delivery_price_rub__isnull=True
        )
        logger.info("Найдено посылок для перерасчёта: %s", packages.count())
        for p in packages:
            cost = (
                p.weight_kg * decimal.Decimal("0.5") + p.content_price_usd * decimal.Decimal("0.01")
            ) * usd_rate
            p.delivery_price_rub = cost.quantize(decimal.Decimal("0.01"))
            p.save(update_fields=["delivery_price_rub"])
        logger.info("Перерасчёт стоимости доставки завершён")
