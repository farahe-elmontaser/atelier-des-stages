# Image du BACKEND (Python + FastAPI)
FROM python:3.12-slim

# Pas de fichiers .pyc, logs affiches tout de suite
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STOCKAGE_DIR=/app/stockage

WORKDIR /app

# 1) Les bibliotheques d'abord (mises en cache par Docker tant que requirements.txt ne change pas)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2) Puis le code
COPY app ./app
COPY data ./data
COPY tests ./tests

# Securite : on ne tourne pas en "root" dans le conteneur
RUN useradd --create-home atelier && mkdir -p /app/stockage && chown -R atelier /app/stockage
USER atelier

EXPOSE 8000

# Docker verifie toutes les 30 s que l'API repond
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/profils')" || exit 1

# 1 seul worker (le scheduler ne doit tourner qu'une fois)
# --proxy-headers : lit la vraie IP du visiteur transmise par le conteneur Nginx
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--proxy-headers", "--forwarded-allow-ips", "*"]
