# Système de Cache avec Redis

Ce projet utilise Redis comme système de cache pour améliorer les performances de l'API. Le caching permet de réduire la charge sur la base de données et d'accélérer les réponses pour les requêtes fréquentes.

## Architecture

Le système de cache est composé de plusieurs éléments :

1. **Client Redis** : Un client connecté au serveur Redis configuré dans `core/cache.py`
2. **Middleware de cache** : Un middleware FastAPI qui met en cache les réponses HTTP dans `api/middlewares/cache.py`
3. **Décorateur de cache** : Un décorateur Python pour mettre en cache les résultats de fonctions dans `api/decorators/cache.py`
4. **Endpoints de gestion** : Des routes API pour visualiser et gérer le cache dans `api/v1/endpoints/cache.py`

## Configuration

Le cache est configuré via les variables d'environnement suivantes :

```
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=redis123
REDIS_DB=0
```

## Stratégie de Cache

Le projet utilise plusieurs stratégies de cache :

### 1. Cache de niveau middleware

Le middleware `CacheMiddleware` met en cache les réponses HTTP complètes pour les requêtes GET. Ce cache est configuré pour :

- Mettre en cache les routes correspondant à certains patterns (`/api/v1/posts`, `/api/v1/tags`)
- Exclure certaines routes (`/docs`, `/openapi.json`, `/metrics`, `/health`, `/api/v1/auth`)
- Expirer après un délai configurable (par défaut 5 minutes)

### 2. Cache au niveau des routes

Les routes individuelles peuvent implémenter leur propre logique de cache, comme démontré dans les routes posts. Cela permet :

- Un contrôle plus fin de ce qui est mis en cache
- Des clés de cache spécifiques à chaque ressource
- Une invalidation précise lors de modifications

### 3. Invalidation de cache

Le cache est invalidé dans les cas suivants :

- Lors de la création, modification ou suppression d'une ressource
- Lorsqu'un administrateur demande explicitement l'invalidation via l'API
- À l'expiration du délai configuré

## Utilisation

### Mise en Cache de Nouvelles Routes

Pour ajouter du cache à une nouvelle route :

```python
from core.cache import redis_client

@router.get("/my-route")
async def get_my_data(request: Request):
    # Vérifier le cache
    cache_key = f"my-data:{param1}:{param2}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Récupérer les données
    data = get_data_from_database()
    
    # Mettre en cache
    redis_client.setex(cache_key, 60 * 5, json.dumps(data))
    
    return data
```

### Utilisation du Décorateur

Pour utiliser le décorateur de cache :

```python
from api.decorators.cache import cache

@router.get("/my-route")
@cache(expire=300, key_prefix="my-data")
async def get_my_data(request: Request):
    # Cette fonction sera mise en cache automatiquement
    return get_data_from_database()
```

### Gestion du Cache

Les administrateurs peuvent gérer le cache via les routes suivantes :

- `GET /api/v1/cache/stats` - Voir les statistiques du cache
- `DELETE /api/v1/cache/clear` - Vider le cache (peut prendre un paramètre `pattern`)

## Bonnes Pratiques

1. **Utilisez des clés de cache descriptives** qui incluent toutes les variables influençant le résultat
2. **Définissez des temps d'expiration appropriés** en fonction de la fréquence de changement des données
3. **Invalidez le cache de manière proactive** lorsque les données sont modifiées
4. **Prévoyez la défaillance de Redis** en ayant un comportement de repli gracieux

## Surveillance

Le système fournit des métriques sur l'utilisation du cache :

- Taux de hit/miss via les headers HTTP (`X-Cache: HIT/MISS`)
- Statistiques de Redis via l'endpoint `/api/v1/cache/stats`
- Logs pour les opérations importantes de cache