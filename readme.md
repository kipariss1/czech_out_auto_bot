# Bot for searching cars in czech republic

Idea:
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
  - Atlas MongoDB
    ...
