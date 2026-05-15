FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .

RUN pip install uv --no-cache-dir && uv pip install --system --no-cache .

COPY . .

CMD ["python", "-m", "bot.main"]