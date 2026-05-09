# MiroFish Russian Speaking Mod

Русскоязычная модификация MiroFish с интеграцией NVIDIA NIM, Docker-деплоем, английскими backend-логами и принудительной генерацией контента на русском языке.

---

# Возможности

- Генерация контента на русском языке
  - персонажи
  - публикации
  - комментарии
  - отчёты
  - мнения
  - результаты симуляции

- Поддержка NVIDIA NIM API
- Docker-деплой
- Английские backend-логи
- Исправления UTF-8 во frontend
- Автовыбор моделей NVIDIA
- Безопасные deployment-скрипты
- Поддержка Docker cache
- Принудительная русификация ответов LLM
- Поддержка памяти графа Zep
- Мультиагентная симуляция

---

# Основные улучшения относительно оригинала

## Принудительная генерация на русском

Весь человекочитаемый контент генерируется на русском языке независимо от языка исходных данных.

JSON-ключи, ID и технические поля не переводятся.

---

## Английские backend-логи

Китайские backend-логи переводятся на английский язык во время работы приложения.

---

## Безопасный Docker deployment

- очистка только своего compose-проекта
- без глобальной очистки Docker
- поддержка кэша сборки
- автоматические redeploy-скрипты

---

## Интеграция NVIDIA NIM

Поддержка NVIDIA-hosted моделей через OpenAI-compatible API.

---

# Требования

- Docker Desktop
- Git
- NVIDIA API key
- Дополнительно:
  - ZEP API key

---

# Быстрый старт

## Клонирование репозитория

```bash
git clone https://github.com/NeoCtepx/MiroFish_Russian_speaking_mod.git
cd MiroFish_Russian_speaking_mod
```

---

## Создание .env

Скопируйте `.env.example` в `.env`

```bash
cp .env.example .env
```

Заполните ключи:

```env
LLM_API_KEY=YOUR_NVIDIA_KEY
LLM_BASE_URL=https://integrate.api.nvidia.com/v1
LLM_MODEL_NAME=YOUR_MODEL

LLM_BOOST_API_KEY=YOUR_NVIDIA_KEY
LLM_BOOST_BASE_URL=https://integrate.api.nvidia.com/v1
LLM_BOOST_MODEL_NAME=YOUR_MODEL

ZEP_API_KEY=OPTIONAL_ZEP_KEY
```

---

## Запуск Docker deployment

```bash
docker compose -p mirofish-nvidia -f docker-compose.nvidia.yml up -d --build
```

---

# Открытие UI

http://127.0.0.1:3000

---

# Важно

- Уже сгенерированные персонажи автоматически не переводятся.
- После включения русификации рекомендуется создавать новый проект.
- Docker build cache сохраняется между пересборками.

---

# Disclaimer

Это модифицированная community-версия MiroFish.

Используйте на свой риск.

---

# Лицензия

Смотрите лицензию оригинального репозитория MiroFish.
