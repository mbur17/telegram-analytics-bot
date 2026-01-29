# Telegram Analytics Bot (NL-to-SQL)

Telegram-бот для аналитики с использованием естественного языка. Преобразует текстовые вопросы в SQL-запросы с помощью **cloud LLM модели qwen3-coder** через Ollama API.

## Технологии

- [Ollama](https://ollama.com) - cloud LLM провайдер
- [Qwen3-Coder](https://github.com/QwenLM/Qwen3-Coder) - модель для генерации SQL
- [Aiogram](https://github.com/aiogram/aiogram) - Telegram Bot framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - SQL toolkit для Python
- [PosgreSQL](https://www.postgresql.org/) - База данных
- [Redis](https://github.com/redis/redis) - In-memory кэш для SQL-результатов
  

## Структура проекта

```
app/
├── alembic/
├── app/
│   ├── bot.py
│   ├── config.py
│   ├── db.py
│   ├── cache.py
│   ├── const.py
│   ├── llm_processor.py
│   └── models.py
├── scripts/
│   └── load_data.py
├── tests/
│   └── test_llm_processor.py
├── data/
│   └── db.json
├── docker-compose.yml
├── Dockerfile
├── init-db.sh
├── requirements.txt
└── .env

# init-db.sh - cкрипт инициализации базы данных.
# Используется для:
# 1. Создания read-only пользователя базы данных (POSTGRES_READONLY_USER),
#    который используется Telegram-ботом.
# 2. Назначения прав только на чтение (SELECT) для всех таблиц схемы.

# db.json — Ваш дамп базы данных проекта (необходимо добавить).
```

## Быстрый старт

На примере аналитики видео-роликов

### Требования
-   Docker и Docker Compose
-   Telegram Bot Token ([@BotFather](https://t.me/BotFather))
-   [Ollama API Key (cloud)](https://ollama.com/settings/keys)

### Запуск за 3 шага
```bash
# 1. Клонировать репозиторий
git clone <your-repo-url>
cd telegram-video-analytics-bot

# 2. Настроить переменные окружения
cp .env.example .env
# Добавить TELEGRAM_BOT_TOKEN и OLLAMA_API_KEY в .env

# 3. Положить данные и запустить
mkdir -p data
cp /path/to/db.json data/
docker-compose up -d
```
**Готово!**
- Запустится PostgreSQL
- Применятся миграции БД
- Загрузятся данные из `db.json`
- Запустится бот

  

## Конфигурация

### Переменные окружения (.env)

Создайте `.env` файл на основе `.env.example`:

```bash
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token_here

# PostgreSQL - Админ юзер
POSTGRES_ADMIN_USER=admin
POSTGRES_ADMIN_PASSWORD=admin_password

# PostgreSQL - Юзер только для чтения
POSTGRES_READONLY_USER=readonly_user
POSTGRES_READONLY_PASSWORD=readonly_password

# PostgreSQL - Основные настройки
POSTGRES_DB=video_analytics
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Ollama конфигурация
OLLAMA_BASE_URL=https://ollama.com
OLLAMA_MODEL=qwen3-coder:480b-cloud # требуется облачная модель
OLLAMA_IMAGE=ollama/ollama:latest
OLLAMA_API_KEY=your_ollama_api_key_here

# Redis
REDIS_URL=redis://redis:6379/0
CACHE_TTL=86400
```
 
## Docker сервисы

```yaml
services:
  redis:         # Redis 7 (кэш)
  postgres:      # PostgreSQL 16
  migrations:    # Применение миграций (admin user)
  data-loader:   # Загрузка данных (admin user)
  bot:           # Telegram бот (readonly user, cloud LLM)
```

## Архитектура

### Общая схема

```
┌─────────────┐
│ Telegram    │
│ User        │
└──────┬──────┘
       ▼
┌───────────────────────────────┐
│ Telegram Bot (aiogram)        │
└──────┬────────────────────────┘
       ▼
┌───────────────────────────────┐
│ Redis Cache                   │
│ - NL → SQL                    │
│ - SQL → Result                │
└──────┬───────────────┬────────┘
       │ cache hit     │ cache miss
       ▼               ▼
┌───────────────────────────────┐
│ LLM Processor                 │
│ (Ollama Cloud)                │
└──────┬────────────────────────┘
       ▼
┌───────────────────────────────┐
│ SQL Validator                 │
└──────┬────────────────────────┘
       ▼
┌───────────────────────────────┐
│ PostgreSQL (readonly user)    │
└──────┬────────────────────────┘
       ▼
┌───────────────────────────────┐
│ Redis Cache (store result)    │
└──────┬────────────────────────┘
       ▼
┌───────────────────────────────┐
│ User получает ответ           │
└───────────────────────────────┘
```

### Примеры запросов

```sql
"Сколько всего видео есть в системе?"
→ SELECT COUNT(*) FROM videos

"Сколько видео набрало больше 100000 просмотров?"
→ SELECT COUNT(*) FROM videos WHERE views_count > 100000

"На сколько просмотров выросли все видео 28 ноября 2025?"
→ SELECT COALESCE(SUM(delta_views_count), 0) 
   FROM video_snapshots 
   WHERE DATE(created_at) = '2025-11-28'
```

### Компоненты

#### 1. **Telegram Bot** (`app/bot.py`)
- Использует aiogram 3.x (асинхронный)
- Обрабатывает команды `/start`, `/help`, `/clear_cache`
- Принимает текстовые вопросы на русском
- Отправляет результат пользователю

#### 2. **LLM Processor** (`app/llm_processor.py`)
- Преобразует естественный язык → SQL
- Использует Ollama + Qwen3-coder (облачный)
- Валидирует сгенерированный SQL


**Ключевые особенности:**

-  **Промпт-инженеринг**: Детальное описание схемы БД + инструкции + примеры запросов
-  **Обработка дат**: "28 ноября 2025" → "2025-11-28"
-  **Безопасность**: Только SELECT запросы, блокировка опасных операций

  

**Пример промпта для Qwen3-Coder:**

```
### Task
Generate a SQL query to answer: "Сколько видео набрало больше 100000 просмотров?"

### Database Schema
CREATE TABLE videos (
id VARCHAR(36) PRIMARY KEY,
creator_id VARCHAR(32) NOT NULL,
views_count BIGINT NOT NULL,
...
);

### Instructions
- Return ONLY the SQL query
- The query must return a single number
- Use COALESCE for NULL handling

### Examples
Question: "How many videos got more than 100000 views?"
SQL: SELECT COUNT(*) FROM videos WHERE views_count > 100000
...

### SQL Query
```

#### 3. **Database Layer** (`app/db.py`)

  

- SQLAlchemy 2.0 с asyncpg (асинхронный драйвер PostgreSQL)

-  **Два режима подключения:**

-  **Admin** (для миграций и загрузки данных) - полные права

-  **Readonly** (для бота) - только SELECT

**Безопасность на уровне БД:**

```python
# Бот использует readonly пользователя
db.init(use_admin=False)

# Даже если LLM сгенерирует DROP TABLE
# PostgreSQL откажет: "permission denied"
```

#### 4. **Models** (`app/models.py`)

- SQLAlchemy ORM модели
- Две таблицы: `videos` и `video_snapshots`
- Индексы для оптимизации запросов

#### 5. **Cache Layer** (`app/cache.py`)

- Redis 7 (in-memory)
- Асинхронный клиент
- TTL для всех ключей
- Кэширования результатов SQL-запросов


## Безопасность

  

### Разделение полномочий

Проект использует **два PostgreSQL пользователя**:

1.  **Admin** (`admin:admin_password`)
- Полные права на БД
- Используется ТОЛЬКО для:
- Применения миграций (`migrations` контейнер)
- Загрузки данных (`data-loader` контейнер)

2.  **Readonly** (`readonly_user:readonly_password`)
- Только `SELECT` на все таблицы
- Используется ботом для выполнения запросов
-  **НЕ МОЖЕТ** выполнить `INSERT`, `UPDATE`, `DELETE`, `DROP`

### Многоуровневая защита

```
┌─────────────────────────────────────┐
│ Уровень 0: Redis Cache              │
│ - Повторные запросы не доходят      │
│ до LLM и БД                         │
└─────────────┬───────────────────────┘
              ▼
┌─────────────────────────────────────┐
│ Уровень 1: SQL Validator (Python)   │
│ - Блокирует не-SELECT запросы       │
│ - Проверяет опасные ключевые слова  │
└─────────────┬───────────────────────┘
              ▼
┌─────────────────────────────────────┐
│ Уровень 2: PostgreSQL permissions   │
│ - Readonly user физически не может  │
│ изменить данные                     │
└─────────────────────────────────────┘
```

**Пример:**

Если LLM ошибётся и сгенерирует:

```sql
DELETE  FROM videos WHERE id = '123'
```

1. SQL Validator откажет: "Non-SELECT query rejected"
2. Если валидатор пропустит → PostgreSQL откажет: "permission denied for table videos"
 
## Примеры запросов

Бот понимает вопросы на русском:

```sql
"Сколько всего видео есть в системе?"
→ SELECT COUNT(*) FROM videos;

"Сколько видео набрало больше 100000 просмотров?"
→ SELECT COUNT(*) FROM videos WHERE views_count > 100000;

"На сколько просмотров выросли все видео 28 ноября 2025?"
→ SELECT COALESCE(SUM(delta_views_count), 0) 
   FROM video_snapshots 
   WHERE DATE(created_at) = '2025-11-28';
```
  

## Управление


### Основные команды

```bash
# Запустить всё
docker-compose  up  -d

# Остановить
docker-compose  down

# Посмотреть логи
docker-compose  logs  -f  bot

# Перезапустить бота
docker-compose  restart  bot

# Проверить статус
docker-compose  ps
```

## Тестирование LLM процессора

```bash
# Запустить тесты
docker-compose  run  --rm  bot  pytest

# Тесты с подробным выводом
docker-compose  run  --rm  bot  pytest  -v
```
