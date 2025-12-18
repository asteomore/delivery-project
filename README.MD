# Сервис международной доставки посылок

Микросервис для расчёта стоимости доставки посылок с автоматическим обновлением курсов валют.

## Описание

Сервис позволяет:
- Регистрировать посылки с автоматической валидацией данных
- Получать список типов посылок (одежда, электроника, разное)
- Просматривать свои посылки с фильтрацией и пагинацией
- Автоматически рассчитывать стоимость доставки по курсу ЦБ РФ

**Особенности:**
- Работа без авторизации (на основе сессий)
- Периодический автоматический пересчёт стоимости доставки каждые 5 минут
- Кэширование курса валют в Redis
- Полная документация API через Swagger
- Масштабируемая архитектура с репликами сервисов
- Доп.задание: конкурентная привязка посылки к транспортной компании с гарантией “первый успевший” (через транзакцию и `SELECT ... FOR UPDATE`)

## Технологический стек

- **Backend:** Python 3.13, Django 6.0, Django REST Framework 3.16
- **Database:** MySQL 9.5
- **Cache/Queue:** Redis 8.4
- **Task Queue:** Celery 5.6 + Beat (Redis как брокер и backend)
- **Documentation:** drf-spectacular (OpenAPI 3.0)
- **Web Server:** Gunicorn
- **Containerization:** Docker + Docker Compose
- **Testing:** pytest, pytest-django, pytest-cov
- **Code Quality:** Ruff

## Быстрый старт

### Предварительные требования

- Docker 20.10+
- Docker Compose 2.0+

### Установка и запуск

1. **Клонируйте репозиторий:**
   ```bash
   git clone <repository-url>
   cd delivery-project
   ```

2. **Создайте файл окружения:**
   ```bash
   cp .env.docker.example .env.docker
   ```
   
   При необходимости отредактируйте `.env.docker` (для dev-окружения можно оставить по умолчанию).

3. **Запустите все сервисы:**
   ```bash
   docker-compose up --build -d
   ```

4. **Дождитесь инициализации:**
   - Миграции БД применятся автоматически
   - Типы посылок будут созданы
   - Статика соберётся

5. **Сервис готов к работе!**
   - API: http://localhost:8000/api/v1/
   - Swagger UI: http://localhost:8000/api/v1/schema/swagger-ui/
   - Django Admin: http://localhost:8000/admin/

### Создание суперпользователя (для админки)

```bash
docker-compose exec web sh -c "cd delivery_service && python manage.py createsuperuser"
```

## API Endpoints

### Основные endpoints:

| Метод | URL | Описание |
|-------|-----|----------|
| `GET` | `/api/v1/package-types/` | Список типов посылок |
| `POST` | `/api/v1/packages/` | Создать посылку |
| `GET` | `/api/v1/packages/` | Список посылок (с фильтрами) |
| `GET` | `/api/v1/packages/{id}/` | Детали посылки |
| `POST` | `/api/v1/debug/recalculate-delivery/` | Пересчёт стоимости вручную |
| `POST` | `/api/v1/packages/{id}/assign-company/` | Привязать посылку к транспортной компании |

### Примеры использования:

**1. Получить типы посылок:**
```bash
curl http://localhost:8000/api/v1/package-types/
```

**2. Создать посылку:**
```bash
curl -X POST http://localhost:8000/api/v1/packages/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ноутбук MacBook",
    "weight_kg": "2.5",
    "content_price_usd": "2000.00",
    "package_type_id": 2
  }'
```

**3. Получить список своих посылок:**
```bash
curl http://localhost:8000/api/v1/packages/
```

**4. Фильтрация посылок:**
```bash
# По типу
curl http://localhost:8000/api/v1/packages/?package_type_id=2

# По наличию рассчитанной стоимости
curl http://localhost:8000/api/v1/packages/?has_delivery_price=yes

# С пагинацией
curl http://localhost:8000/api/v1/packages/?page=2
```

**5. Получить детали посылки:**
```bash
curl http://localhost:8000/api/v1/packages/1/
```

**6. Запустить пересчёт стоимости вручную (для отладки):**
```bash
curl -X POST http://localhost:8000/api/v1/debug/recalculate-delivery/
```
**7. Привязать посылку к транспортной компании:**
```bash
curl -X POST http://localhost:8000/api/v1/packages/1/assign-company/ \
  -H "Content-Type: application/json" \
  -d '{ "company_id": 123 }'
```

### Формат ответа

Все ответы API имеют единообразный формат:

**Успешный ответ:**
```json
{
  "status": true,
  "data": { ... },
  "error": null
}
```

**Ответ с ошибкой:**
```json
{
  "status": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Описание ошибки",
    "details": { ... }
  }
}
```

##  Тестирование

### Запуск всех тестов:
```bash
docker-compose run --rm web sh -c "cd delivery_service && pytest"
```

### Запуск с покрытием:
```bash
docker-compose run --rm web sh -c "cd delivery_service && pytest --cov=packages --cov-report=html"
```

### Запуск конкретного теста:
```bash
docker-compose run --rm web sh -c "cd delivery_service && pytest tests/test_api.py::TestPackagesAPI::test_create_package_success -v"
```

##  Мониторинг

### Проверка состояния сервисов:
```bash
docker-compose ps
```

### Логи:
```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f web
docker-compose logs -f celery
docker-compose logs -f celery-beat
```

### Логи внутри контейнера:
- Приложение: `delivery_service/logs/app.log`
- Celery: `delivery_service/logs/celery.log`

### Проверка healthcheck:
```bash
# Web
curl http://localhost:8000/api/v1/package-types/

# Redis
docker-compose exec redis redis-cli ping

# MySQL
docker-compose exec db mysqladmin ping -h localhost -u root -prootpassword
```

##  Архитектура

### Компоненты системы:

- **web** (4 реплики) - Django приложение с Gunicorn
- **celery** (4 реплики) - Воркеры для фоновых задач
- **celery-beat** - Планировщик периодических задач
- **db** - MySQL база данных
- **redis** - Кэш и брокер сообщений

### Периодические задачи:

- **update_packages_delivery_price** - каждые 5 минут
  - Получает курс USD/RUB из Redis (или обновляет через API ЦБ РФ)
  - Рассчитывает стоимость доставки для необработанных посылок
  - Использует `select_for_update(skip_locked=True)` для предотвращения конфликтов
  - Основной расчёт цены идёт через Celery-задачу, а дополнительный роут
  /debug/recalculate-delivery/ позволяет руками переинициализировать перерасчёт.

### Формула расчёта стоимости:

```
Стоимость = (вес_кг × 0.5 + стоимость_usd × 0.01) × курс_usd_rub
```

##  Структура проекта

```
delivery-project/
├── delivery_service/          # Django приложение
│   ├── delivery_service/      # Настройки проекта
│   │   ├── settings.py        # Конфигурация Django
│   │   ├── celery.py          # Конфигурация Celery
│   │   └── urls.py            # Главные URL patterns
│   ├── packages/              # Основное приложение
│   │   ├── models.py          # Модели Package, PackageType
│   │   ├── serializers.py     # DRF сериализаторы
│   │   ├── views.py           # API views
│   │   ├── tasks.py           # Celery задачи
│   │   ├── utils.py           # Утилиты (api_response)
│   │   └── exceptions.py      # Обработка исключений
│   ├── tests/                 # Тесты
│   │   ├── conftest.py        # Pytest fixtures
│   │   ├── test_api.py        # Тесты API
│   │   └── test_tasks.py      # Тесты Celery задач
│   └── manage.py              # Django management команды
├── docker/                    # Docker конфигурация
│   └── mysql-init/            # SQL скрипты инициализации
├── docker-compose.yml         # Оркестрация сервисов
├── Dockerfile                 # Образ приложения
├── requirements.txt           # Python зависимости
├── pyproject.toml             # Poetry & Ruff конфигурация
└── README.md                  # Этот файл
```

## Конфигурация

### Переменные окружения (.env.docker):

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `SECRET_KEY` | Django secret key |  |
| `DEBUG` | Режим отладки | `False` |
| `ALLOWED_HOSTS` | Разрешённые хосты | `localhost` |
| `DB_ENGINE` | БД движок | `django.db.backends.mysql` |
| `DB_NAME` | Имя БД |  |
| `DB_USER` | Пользователь БД |  |
| `DB_PASSWORD` | Пароль БД |  |
| `DB_HOST` | Хост БД | `db` |
| `DB_PORT` | Порт БД | `3306` |
| `REDIS_URL` | URL Redis для кэша | `redis://redis:6379/1` |
| `CELERY_BROKER_URL` | URL брокера Celery | `redis://redis:6379/0` |
| `CELERY_RESULT_BACKEND` | Backend для результатов | `redis://redis:6379/1` |

##  Разработка

### Локальная разработка без Docker:

1. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   # или
   poetry install
   ```

2. **Создайте `.env` файл:**
   ```bash
   cp .env.example .env
   ```

3. **Запустите зависимости:**
   ```bash
   # MySQL и Redis через Docker
   docker-compose up db redis
   ```

4. **Примените миграции:**
   ```bash
   cd delivery_service
   python manage.py migrate
   python manage.py init_package_types
   ```

5. **Запустите сервер:**
   ```bash
   python manage.py runserver
   ```

6. **Запустите Celery (в отдельных терминалах):**
   ```bash
   celery -A delivery_service worker -l info
   celery -A delivery_service beat -l info
   ```

## Документация API

Полная документация доступна через Swagger UI:
- **Swagger UI:** http://localhost:8000/api/v1/schema/swagger-ui/
- **OpenAPI Schema:** http://localhost:8000/api/v1/schema/

##  Безопасность

- Приложение работает от непривилегированного пользователя в Docker
- Секретные данные через переменные окружения
- CSRF защита включена
- Secure cookies в production режиме
- Валидация всех входных данных



**Версия:** 1.0.0