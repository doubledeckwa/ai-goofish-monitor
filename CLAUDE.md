# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

based on Playwright + AI Xianyu intelligent monitoring robot。FastAPI rear end + Vue 3 Front-end, supports multi-task concurrent monitoring、multimodal AI Product analysis, multi-channel notification push。

## core architecture

```
APIlayer (src/api/routes/)
    ↓
service layer (src/services/)
    ↓
Domain layer (src/domain/)
    ↓
infrastructure layer (src/infrastructure/)
```

key entrance：
- `src/app.py` - FastAPI Application main entrance
- `spider_v2.py` - reptile CLI Entrance
- `src/scraper.py` - Playwright Reptile core logic

service layer：
- `TaskService` - Task CRUD
- `ProcessService` - Reptile sub-process management
- `SchedulerService` - APScheduler Timing scheduling
- `AIAnalysisService` - multimodal AI analyze
- `NotificationService` - Multi-channel notifications（ntfy/Bark/Enterprise WeChat/Telegram/Webhook）

front end (`web-ui/`)：Vue 3 + Vite + shadcn-vue + Tailwind CSS

## development command

```bash
# backend development
python -m src.app
# or
uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload

# Front-end development
cd web-ui && npm install && npm run dev

# Front-end build
cd web-ui && npm run build

# One-click local startup (build front-end + Start backend）
bash start.sh

# Docker deploy
docker compose up --build -d
```

## crawler command

```bash
python spider_v2.py                          # Run all enabled tasks
python spider_v2.py --task-name "MacBook"    # Run specified task
python spider_v2.py --debug-limit 3          # Debug mode, limit the number of products
python spider_v2.py --config custom.json     # Custom configuration file
```

## test

```bash
pytest                              # Run all tests
pytest --cov=src                    # 覆盖率报告
pytest tests/unit/test_utils.py    # Run a single test file
pytest tests/unit/test_utils.py::test_safe_get  # Run a single test function
```

Test Specification: Documentation `tests/**/test_*.py`，function `test_*`

## Configuration

environment variables (`.env`)：
- AI Model：`OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL_NAME`
- notify：`NTFY_TOPIC_URL`, `BARK_URL`, `WX_BOT_URL`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
- reptile：`RUN_HEADLESS`, `LOGIN_IS_EDGE`
- Web Certification：`WEB_USERNAME`, `WEB_PASSWORD`
- port：`SERVER_PORT`

Task configuration (`config.json`)：Define monitoring tasks (keywords、price range、cron expression、AI prompt Documents, etc.）

## data flow

1. Web UI / config.json Create task
2. SchedulerService according to cron Trigger or manual start
3. ProcessService start up spider_v2.py child process
4. scraper.py use Playwright Grab products
5. AIAnalysisService Call multimodal model analysis
6. NotificationService Push qualified products
7. Result storage：`jsonl/`（data）、`images/`（picture）、`logs/`（log）

## Things to note

- AI The model must support image upload (multi-modal）
- Docker Deployment requires passing Web UI Manually update login status（`state.json`）
- Set when encountering sliding verification code `RUN_HEADLESS=false` Manual processing
- The production environment must be modified from the default Web Authentication password
