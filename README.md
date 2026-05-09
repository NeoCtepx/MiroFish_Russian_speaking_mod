# MiroFish Russian Speaking Mod

Russian-speaking modified version of MiroFish with NVIDIA NIM integration, Docker deployment, English backend logs and forced Russian AI-generated simulation output.

---

# Features

- Russian AI-generated content
  - agent personas
  - publications
  - comments
  - reports
  - opinions
  - simulation outputs

- NVIDIA NIM API support
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

# Main Improvements Over Original

## Russian output enforcement

All generated human-readable content is forced to Russian regardless of seed/source language.

JSON keys, IDs and technical fields remain unchanged.

---

## English backend logs

Chinese backend logs are translated into English during runtime.

---

## Safer Docker deployment

- isolated Docker project cleanup
- no global Docker cleanup
- cache-friendly rebuilds
- automatic redeploy scripts

---

## NVIDIA NIM integration

Supports NVIDIA hosted models through OpenAI-compatible API.

---

# Requirements

- Docker Desktop
- Git
- NVIDIA API key
- Optional:
  - ZEP API key

---

# Quick Start

## Clone repository

```bash
git clone https://github.com/NeoCtepx/MiroFish_Russian_speaking_mod.git
cd MiroFish_Russian_speaking_mod
```

---

## Create .env

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

## Start Docker deployment

```bash
docker compose -p mirofish-nvidia -f docker-compose.nvidia.yml up -d --build
```

---

# Open UI

http://127.0.0.1:3000

---

# Notes

- Existing generated personas are not automatically translated.
- Create a new project after enabling Russian output enforcement.
- Docker build cache is preserved between rebuilds.

---

# Disclaimer

This repository is a modified community version of MiroFish.

Use at your own risk.

---

# License

See original MiroFish repository license.
