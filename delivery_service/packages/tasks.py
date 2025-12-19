import decimal
import logging

import redis
import requests
from celery import shared_task
from django.conf import settings
from django.db import DatabaseError, transaction

from .models import Package

logger = logging.getLogger("packages")
redis_client = redis.from_url(getattr(settings, "REDIS_URL", settings.CELERY_BROKER_URL))
USD_RATE_KEY = "usd_rub_rate"


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def update_usd_rate(self):
    """Обновить курс USD/RUB и сохранить его в Redis."""
    try:
        resp = requests.get("https://www.cbr-xml-daily.ru/daily_json.js", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        usd_rate = data["Valute"]["USD"]["Value"]
    except (requests.RequestException, ValueError, KeyError) as exc:
        logger.exception("Не удалось получить курс USD/RUB с сервера ЦБ")
        raise self.retry(exc=exc)

    try:
        redis_client.set(USD_RATE_KEY, usd_rate, ex=60 * 6)
    except redis.RedisError:
        logger.exception("Не удалось обновить курс USD/RUB")

    logger.info("Курс USD/RUB обновлён: %s", usd_rate)
    return usd_rate


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def update_packages_delivery_price(self):
    """Рассчитать стоимость доставки для всех посылок без цены, используя курс из Redis."""
    try:
        try:
            rate_bytes = redis_client.get(USD_RATE_KEY)
        except redis.RedisError:
            logger.exception("Ошибка при чтении курса USD/RUB из Redis")
            rate_bytes = None

        if rate_bytes is None:
            raw_rate = update_usd_rate()
            if raw_rate is None:
                logger.warning("Пропускаю перерасчёт: нет курса USD/RUB")
                return
            usd_rate = decimal.Decimal(str(raw_rate))
        else:
            usd_rate = decimal.Decimal(rate_bytes.decode("utf-8"))

        logger.info("Запуск перерасчёта стоимости доставки, курс USD/RUB: %s", usd_rate)

        try:
            with transaction.atomic():
                packages = Package.objects.select_for_update(skip_locked=True).filter(
                    delivery_price_rub__isnull=True
                )

                to_update = []
                for p in packages:
                    cost = (
                        p.weight_kg * decimal.Decimal("0.5")
                        + p.content_price_usd * decimal.Decimal("0.01")
                    ) * usd_rate
                    p.delivery_price_rub = cost.quantize(decimal.Decimal("0.01"))
                    to_update.append(p)

                logger.info("Найдено посылок для перерасчёта: %s", len(to_update))
                if to_update:
                    Package.objects.bulk_update(to_update, ["delivery_price_rub"])
        except DatabaseError:
            logger.exception("Ошибка БД при перерасчёте стоимости доставки")

        logger.info("Перерасчёт стоимости доставки завершён")

    except (redis.RedisError, DatabaseError) as exc:
        logger.exception("Критическая ошибка инфраструктуры при перерасчёте")
        raise self.retry(exc=exc)
