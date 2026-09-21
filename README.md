# Сервис управления рассылками (MailingService)

Веб-приложение на Django для управления клиентами, сообщениями и рассылками,
с ручным и командным запуском отправки, ролями пользователей и статистикой.

## Стек
- Python 3.11, Django 5.2
- PostgreSQL
- Django cache framework (LocMemCache; для продакшена рекомендуется Redis)
- SMTP (Gmail) для реальной отправки писем

## Структура проекта
```
config/     — настройки проекта, корневой urls.py
users/      — кастомная модель пользователя, регистрация/подтверждение email,
              вход/выход, восстановление пароля, роль менеджера (setup_roles)
clients/    — модель "Получатель рассылки" и CRUD
mailing/    — модели "Сообщение", "Рассылка", "Попытка рассылки", CRUD,
              логика отправки (services.py), management-команда send_mailings,
              кэшированная статистика
templates/  — HTML-шаблоны (base.html + по разделам)
static/     — статика (css/style.css)
```

## Установка и запуск

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Создайте `.env` в корне проекта:
```
secret_key=<django secret key>
debug=True

db_user=<postgres user>
db_password=<postgres password>
db_host=localhost
db_port=5432

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=<app password, см. раздел про Gmail ниже>

cache_enabled=True
```

Поднимите базу и накатите миграции:
```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py setup_roles      # создаёт группу "Менеджеры" с нужными правами
python manage.py runserver
```

Откройте http://127.0.0.1:8000/

## Настройка реальной отправки писем (Gmail)

Обычный пароль от Gmail не подходит — нужен **пароль приложения**:
1. Включите двухфакторную аутентификацию на аккаунте Gmail.
2. Перейдите на https://myaccount.google.com/apppasswords и создайте пароль приложения.
3. Впишите его в `.env` в `EMAIL_HOST_PASSWORD` **без пробелов**.

Проверить, что SMTP настроен верно, без запуска сервера:
```powershell
python manage.py sendtestemail your_real_email@example.com
```
Если письмо дошло — конфигурация SMTP верна.

## Роли пользователей
- **Обычный пользователь** — управляет только своими клиентами, сообщениями и рассылками
  (создание/просмотр/редактирование/удаление, ручной запуск отправки).
- **Менеджер** (группа «Менеджеры» или `is_staff`) — видит все рассылки/клиентов/сообщения,
  может отключать/включать чужие рассылки, но не редактирует и не удаляет чужой контент.

Назначить пользователя менеджером — добавить его в группу «Менеджеры» через `/admin/`
(группа создаётся командой `python manage.py setup_roles`).

## Запуск рассылки

Через интерфейс — кнопка «Отправить сейчас» на странице рассылки (`/mailings/<id>/`).
Кнопка видна только владельцу рассылки или менеджеру/staff.

Через командную строку:
```bash
python manage.py send_mailings           # отправить все рассылки со статусом "Запущена"
python manage.py send_mailings <id>      # отправить конкретную рассылку
```

Отправка возможна только если текущее время находится в интервале `[start_time, end_time]`
и рассылка активна — иначе выводится ошибка. Для каждого получателя создаётся запись
"Попытка рассылки" (успех/ошибка), все записи одной отправки сохраняются в БД одним
батчем через `bulk_create`.

**Важно:** повторное нажатие «Отправить сейчас» отправляет письма заново каждый раз —
дедупликации нет, это нужно учитывать при ручном тестировании на реальных ящиках.

## Кэширование статистики

Страница `/stats/` показывает агрегаты (число рассылок, активных рассылок, уникальных
получателей), которые кэшируются на 60 секунд через низкоуровневый API Django (`cache.get`/
`cache.set`). При создании, изменении, удалении рассылки или переключении её активности
кэш инвалидируется принудительно, чтобы не показывать устаревшие цифры. Кэш можно
отключить через `.env`:
```
cache_enabled=False
```

## Troubleshooting (реальные проблемы, встреченные при разработке)

Собрано по мере отладки — если столкнётесь с похожим, экономит время.

### `TemplateDoesNotExist: mailing/home.html`
`TEMPLATES.DIRS` в `settings.py` должен указывать на общую папку шаблонов проекта:
```python
TEMPLATES = [
    {
        ...
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        ...
    },
]
```
Без этого Django ищет шаблоны только внутри `<app>/templates/<app>/`, а не в
`templates/` на уровне проекта.

### `AppRegistryNotReady: Apps aren't loaded yet.`
В `<app>/apps.py` не должно быть ничего, кроме класса `AppConfig`. Импорт форм/моделей
на уровне модуля `apps.py` ломает загрузку приложений — Django импортирует `apps.py`
раньше, чем реестр приложений готов. Формы, модели и т.п. — только в `forms.py`,
`models.py`, `views.py`.

### `models.W042: Auto-created primary key used when not defining a primary key type`
В `<app>/apps.py` не хватает:
```python
default_auto_field = 'django.db.models.BigAutoField'
```
Проверьте, что эта строка есть во всех `apps.py` (`users`, `clients`, `mailing`),
не только в некоторых.

### `Permission.DoesNotExist` в `setup_roles`
Права (`view_<model>`, `change_<model>`) создаются автоматически только при выполнении
`python manage.py migrate`, а не при `makemigrations`. Если добавили новую модель —
сначала `makemigrations` + `migrate`, и только потом `setup_roles`.

### `AttributeError: module 'django.core.cache' has no attribute 'delete'`
Неверный импорт кэша:
```python
from django.core import cache        # импортирует модуль — НЕПРАВИЛЬНО
```
Правильно:
```python
from django.core.cache import cache  # импортирует объект кэша
```

### Письма продолжают печататься в консоль, хотя `EMAIL_BACKEND` в `.env` заменён на SMTP
Автоперезагрузчик Django (`StatReloader`) реагирует на изменения `.py`-файлов, но
**не перечитывает `.env`**. После правки `.env` нужен полный перезапуск процесса
(`Ctrl+C` → `python manage.py runserver`), а не просто сохранение файла.

Проверить, какой backend реально используется прямо сейчас, можно в отдельном
процессе (он всегда читает `.env` заново):
```powershell
python manage.py shell
```
```python
from django.conf import settings
print(settings.EMAIL_BACKEND)
```

### Рассылка не отправляется, хотя кнопка нажата, ошибок нет
Проверьте статус рассылки — отправка разрешена только если `start_time <= now <= end_time`:
```python
from django.utils import timezone
from mailing.models import Mailing
m = Mailing.objects.get(pk=<id>)
print(m.start_time, m.end_time, timezone.now(), m.status, m.is_sendable_now())
```

### Разовый `django.db.utils.OperationalError` при обращении к БД
Если ошибка возникла один раз и следующий же запрос прошёл успешно — это кратковременный
обрыв соединения с PostgreSQL (не связано с кодом приложения). Если повторяется
регулярно — смотрите логи службы PostgreSQL и `SELECT count(*) FROM pg_stat_activity;`
на предмет исчерпания `max_connections`.

## Соответствие критериям оценки

| Критерий | Реализация |
|---|---|
| Модель реализована, поля соответствуют заданию | `clients.Client`, `mailing.Message`, `mailing.Mailing`, `mailing.MailingAttempt` |
| Обработчик: письмо каждому получателю | `mailing/services.py::send_mailing` |
| Валидация времени вызова обработчика | `Mailing.is_sendable_now()` + `MailingNotAllowedError` в `services.py` |
| Попытка отправки создаётся через batch | `MailingAttempt.objects.bulk_create(...)` в `services.py` |
| Регистрация, подтверждение email, вход/выход, восстановление пароля | приложение `users` |
| Необходимая информация сохраняется в БД | миграции всех моделей (`*/migrations`) |
| Доступ по ролям | `OwnerRequiredMixin`, проверки `is_staff`/`is_manager`, команда `setup_roles` |
| Данные из кэша | `mailing.views.StatsView` — низкоуровневый Django cache API с инвалидацией |

## Полезные команды

```bash
python manage.py check                          # проверка проекта на ошибки конфигурации
python manage.py makemigrations --check --dry-run   # проверка, что все миграции созданы
python manage.py sendtestemail you@example.com   # быстрая проверка SMTP без веб-интерфейса
python manage.py setup_roles                     # создание/обновление группы "Менеджеры"
python manage.py send_mailings                    # запуск всех активных рассылок из CLI
```
