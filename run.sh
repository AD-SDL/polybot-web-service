export LOG_NAME=polybot.log
export REDIS_URL=redis://localhost
uvicorn polybot.fastapi:app
