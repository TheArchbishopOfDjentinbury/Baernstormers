uvicorn main:app --reload
set -a
source .env
set +a
uv run main.py
