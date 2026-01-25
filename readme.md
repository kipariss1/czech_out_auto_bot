## Bot for searching cars in czech republic

✅It's Webapp, Telegram Bot and Postgres DB running in separate containers with e2e tests pipeline for webapp.
~~For now it's PoC webapp & bot running in one container.~~

TODO:
 - separate containers for web_app, telegram bot and db ✅
 - grown up db ✅
 - implement smoke tests for web app ✅
 - implement jobs for scrapping bazos.cz and processing it with LLM & sending to user (parser & worker)

Original Idea:
 - parse bazos, sauto ..., run it throught some LLM
 - ask if it's a car or a carpart
 - extract info about advertisement like this:
 {
  "brand": "Škoda",
  "model": "Fabia",
  "engine": "1.4",
  "year": 2009,
  "mileage": 27000
}
- store it into vector database
- do it periodically for search and add new ones for the search
- do the filtering of the found ones for the search

  Possible stack:
  - FastAPI
  - SQLAlchemy
  - docker
  - Postgres (SQLite for testing)
    ...
