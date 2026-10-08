web: cd apps/api && uvicorn main:app --host 0.0.0.0 --port $PORT
worker: cd apps/api && rq worker --url $REDIS_URL
