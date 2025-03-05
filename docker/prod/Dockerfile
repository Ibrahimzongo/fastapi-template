FROM python:3.11-slim as builder

WORKDIR /app

# Installation des dépendances système minimales pour la compilation
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    default-libmysqlclient-dev \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copier uniquement les fichiers de dépendances pour profiter du cache Docker
COPY requirements/prod.txt .

# Créer des wheels pour toutes les dépendances
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r prod.txt

# Image finale
FROM python:3.11-slim

WORKDIR /app

# Créer un utilisateur non-root
RUN addgroup --system app && adduser --system --group app

# Installation des dépendances runtime minimales
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq5 \
    default-mysql-client \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copier les wheels et installer les dépendances
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache-dir /wheels/*

# Copier le code de l'application
COPY src/ /app/src/
COPY alembic/ /app/alembic/
COPY alembic.ini /app/
COPY scripts/ /app/scripts/
COPY wait-for-it.sh /app/

# Rendre le script d'attente exécutable
RUN chmod +x /app/wait-for-it.sh

# Permissions pour l'utilisateur app
RUN chown -R app:app /app
USER app

# Variables d'environnement
ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Exposer le port
EXPOSE ${PORT}

# Commande de démarrage avec Gunicorn pour la production
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "src.main:app"]