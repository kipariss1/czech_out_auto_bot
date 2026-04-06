# Czech Out Auto Bot

`czech_out_auto_bot` is a car-search assistant for the Czech market.

It combines:
- a FastAPI web app for creating searches
- a Telegram bot for notifications
- a PostgreSQL database for persistent search data
- a parser/worker pipeline for scraping Bazos and filtering ads with an LLM
- automated test coverage for unit, integration, and smoke e2e flows

## What It Does

The app lets a user define a car search with filters such as:
- manufacturer and model
- production year range
- mileage range
- price range
- PSC / search radius

The backend then:
1. collects matching ads from Bazos
2. pushes new ads into a processing queue
3. sends each ad to Ollama for structured extraction and validation
4. checks whether the ad fits an existing user search
5. sends a Telegram notification when a match is found

## Architecture

Relevant code areas:
- [web_app](./web_app) - FastAPI web UI for creating and viewing car searches.
- [telegram_bot](./telegram_bot) - Telegram bot integration used for sending matched-ad notifications.
- [queue_svc/parser](./queue_svc/parser) - parser logic that scans Bazos and pushes new ads into the processing queue.
- [queue_svc/worker](./queue_svc/worker) - worker pipeline that validates queued ads and matches them against user searches.
- [src/models](./src/models) - shared database and domain models used across services.
- [src/database_utils](./src/database_utils) - database access and helper utilities for persistence-related operations.

## Local Run

### Requirements

- Docker and Docker Compose
- Python 3.11 if you want to run tests locally outside containers
- Node.js 20 if you want to run Playwright smoke tests locally

## CI

The GitHub Actions workflow in [tests.yml](./.github/workflows/tests.yml) currently runs:
- unit tests
- integration tests
- smoke e2e tests

## Progress Tracker

TODO:
 - separate containers for web_app, telegram bot and db ✅
 - grown up db ✅
 - implement smoke tests for web app ✅
 - implement jobs for scrapping bazos.cz and processing it with LLM & sending to user (parser & worker) ✅
