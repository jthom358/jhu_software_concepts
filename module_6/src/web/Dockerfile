FROM python:3.11-slim

WORKDIR /app

COPY src/web/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src

RUN addgroup --gid 1000 appgroup \
    && adduser --disabled-password --gecos "" --uid 1000 \
       --gid 1000 appuser \
    && chown -R appuser:appgroup /app

ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

USER 1000

CMD ["python", "-m", "src.web.run"]