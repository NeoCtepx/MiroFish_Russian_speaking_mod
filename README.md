# MiroFish Russian Speaking Mod

---

# English

Russian-speaking modified version of MiroFish with NVIDIA NIM integration, NVIDIA hosted AI models via API, Docker deployment, English backend logs and forced Russian AI-generated simulation output.

---

## Features

- Russian AI-generated content
  - agent personas
  - publications
  - comments
  - reports
  - opinions
  - simulation outputs

- NVIDIA API integration
- NVIDIA hosted AI models support
- NVIDIA NIM support
- OpenAI-compatible API architecture
- Docker deployment
- English backend logs
- UTF-8 frontend fixes
- Automatic model selection support
- Safer deployment scripts
- Persistent Docker cache support
- Runtime language enforcement
- Zep graph memory support
- Multi-agent simulation environment

---

## Main Improvements Over Original

### Russian output enforcement

All generated human-readable content is forced to Russian regardless of seed/source language.

JSON keys, IDs and technical fields remain unchanged.

---

### English backend logs

Chinese backend logs are translated into English during runtime.

---

### Safer Docker deployment

- isolated Docker project cleanup
- no global Docker cleanup
- cache-friendly rebuilds
- automatic redeploy scripts

---

### NVIDIA AI Models via API

The project supports NVIDIA hosted AI models through API access using OpenAI-compatible endpoints.

Can work with:

- NVIDIA NIM
- NVIDIA hosted LLMs
- Multiple NVIDIA model configurations
- Dynamic model switching

---

## Requirements

- Docker Desktop
- Git
- NVIDIA API key
- Optional:
  - ZEP API key

---

## Quick Start

### Clone repository

```bash
git clone https://github.com/NeoCtepx/MiroFish_Russian_speaking_mod.git
cd MiroFish_Russian_speaking_mod
```

---

### Create .env

Copy `.env.example` to `.env`

```bash
cp .env.example .env
```

Fill your keys:

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

### Start Docker deployment

```bash
docker compose -p mirofish-nvidia -f docker-compose.nvidia.yml up -d --build
```

---

## Open UI

http://127.0.0.1:3000

---

# Русский

Русскоязычная модификация MiroFish с интеграцией NVIDIA NIM, использованием AI-моделей NVIDIA через API, Docker-деплоем, английскими backend-логами и принудительной генерацией контента на русском языке.

---

## Возможности

- Генерация контента на русском языке
  - персонажи
  - публикации
  - комментарии
  - отчёты
  - мнения
  - результаты симуляции

- Интеграция NVIDIA API
- Поддержка AI-моделей NVIDIA
- Поддержка NVIDIA NIM
- OpenAI-compatible API архитектура
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

## Основные улучшения относительно оригинала

### Принудительная генерация на русском

Весь человекочитаемый контент генерируется на русском языке независимо от языка исходных данных.

JSON-ключи, ID и технические поля не переводятся.

---

### Английские backend-логи

Китайские backend-логи переводятся на английский язык во время работы приложения.

---

### Безопасный Docker deployment

- очистка только своего compose-проекта
- без глобальной очистки Docker
- поддержка кэша сборки
- автоматические redeploy-скрипты

---

### AI-модели NVIDIA через API

Проект поддерживает AI-модели NVIDIA через API с использованием OpenAI-compatible endpoints.

Поддерживается работа с:

- NVIDIA NIM
- NVIDIA hosted LLMs
- несколькими конфигурациями моделей NVIDIA
- динамическим переключением моделей

---

## Требования

- Docker Desktop
- Git
- NVIDIA API key
- Дополнительно:
  - ZEP API key

---

## Быстрый старт

### Клонирование репозитория

```bash
git clone https://github.com/NeoCtepx/MiroFish_Russian_speaking_mod.git
cd MiroFish_Russian_speaking_mod
```

---

### Создание .env

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

### Запуск Docker deployment

```bash
docker compose -p mirofish-nvidia -f docker-compose.nvidia.yml up -d --build
```

---

## Открытие UI

http://127.0.0.1:3000

---

## Disclaimer

This repository is a modified community version of MiroFish.

Это модифицированная community-версия MiroFish.

Use at your own risk / Используйте на свой риск.
