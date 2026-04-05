FROM python:3.14-slim

WORKDIR /app

COPY pyproject.toml .

RUN pip install uv && uv pip install --system --no-cache .

COPY . .

CMD ["python", "-m", "bot.main"]